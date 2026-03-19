const vscode = require("vscode");
const http = require("http");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

let outputChannel;
let sendtextBridgeServer;
let sendtextBridgeServerStartedAtIso;
let terminalDataWriteEventAvailable = false;
let capturePromiseResolve;

const STATE_KEYS = {
  startedCodex: "ivyhouseTerminalFallback.startedCodex",
  startedCopilot: "ivyhouseTerminalFallback.startedCopilot",
};

const userFacingCommands = [
  "ivyhouseTerminalFallback.startCodex",
  "ivyhouseTerminalFallback.restartCodex",
  "ivyhouseTerminalFallback.startCopilot",
  "ivyhouseTerminalFallback.restartCopilot",
  "ivyhouseTerminalFallback.startAll",
  "ivyhouseTerminalFallback.sendToCodex",
  "ivyhouseTerminalFallback.sendToCopilot",
  "ivyhouseTerminalFallback.captureCodexOutput",
  "ivyhouseTerminalFallback.autoCaptureCodexStatus",
  "ivyhouseTerminalFallback.restartAndCaptureCodexStatus",
  "ivyhouseTerminalFallback.verifyCodexStatusInjection",
  "ivyhouseTerminalFallback.showDiagnostics",
  "ivyhouseTerminalFallback.resetSessionState",
];

const internalCommands = [
  "ivyhouseTerminalFallback.sendLiteral",
  "ivyhouseTerminalFallback.sendLiteralToCodex",
  "ivyhouseTerminalFallback.sendLiteralToCopilot",
  "ivyhouseTerminalFallback.startBridge",
  "ivyhouseTerminalFallback.stopBridge",
];

const shellReadState = {
  attachedExecutionIdByTerminal: new Map(),
  lastAttachedTerminalName: "",
};

let captureState = {
  active: false,
  terminalName: "",
  lastFile: "",
  startedAtMs: 0,
  lastDataAtMs: 0,
  bytesWritten: 0,
  stopTimer: undefined,
};

function getConfig() {
  const cfg = vscode.workspace.getConfiguration("ivyhouseTerminalFallback");
  return {
    codexCommand: cfg.get("codexCommand", "codex"),
    copilotCommand: cfg.get("copilotCommand", "copilot"),
    codexTerminalName: cfg.get("codexTerminalName", "Codex CLI"),
    copilotTerminalName: cfg.get("copilotTerminalName", "Copilot CLI"),
    submitDelayMs: cfg.get("submitDelayMs", 350),
    captureDir: cfg.get("captureDir", ".service/terminal_capture"),
    alwaysCaptureCodex: cfg.get("alwaysCaptureCodex", true),
    alwaysCaptureCopilot: cfg.get("alwaysCaptureCopilot", true),
    captureMaxSeconds: cfg.get("captureMaxSeconds", 10),
    captureSilenceMs: cfg.get("captureSilenceMs", 800),
    captureMaxBytes: cfg.get("captureMaxBytes", 65536),
    bridgePort: cfg.get("bridgePort", 8765),
    bridgeMaxPayloadBytes: cfg.get("bridgeMaxPayloadBytes", 32768),
    bridgeMaxRequestBytes: cfg.get("bridgeMaxRequestBytes", 65536),
    bridgeRateLimit: cfg.get("bridgeRateLimit", 1),
    bridgeRateBurst: cfg.get("bridgeRateBurst", 2),
  };
}

function getWorkspaceRootFsPath() {
  return vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
}

function resolveCapturePaths(cfg) {
  const root = getWorkspaceRootFsPath();
  if (!root) {
    return undefined;
  }

  const dir = path.join(root, cfg.captureDir);
  return {
    dir,
    lastFile: path.join(dir, "codex_last.txt"),
    lastFileDisplay: path.join(cfg.captureDir, "codex_last.txt"),
    liveFile: path.join(dir, "codex_live.txt"),
    liveFileDisplay: path.join(cfg.captureDir, "codex_live.txt"),
    copilotLiveFile: path.join(dir, "copilot_live.txt"),
    copilotLiveFileDisplay: path.join(cfg.captureDir, "copilot_live.txt"),
    debugFile: path.join(dir, "monitor_debug.jsonl"),
    debugFileDisplay: path.join(cfg.captureDir, "monitor_debug.jsonl"),
    bridgeAuditFile: path.join(dir, "sendtext_bridge_events.jsonl"),
    bridgeAuditFileDisplay: path.join(cfg.captureDir, "sendtext_bridge_events.jsonl"),
  };
}

function resolveBridgeTokenPath(rootAbs) {
  return path.join(rootAbs, ".service", "sendtext_bridge", "token");
}

function logLine(message) {
  if (!outputChannel) {
    return;
  }
  outputChannel.appendLine(message);
}

function appendDebugEvent(cfg, event) {
  const paths = resolveCapturePaths(cfg);
  if (!paths) {
    return;
  }

  try {
    fs.mkdirSync(paths.dir, { recursive: true });
    fs.appendFileSync(
      paths.debugFile,
      `${JSON.stringify({ ts: new Date().toISOString(), source: "fallback", ...event })}\n`,
      "utf8",
    );
  } catch {
    // ignore
  }
}

function findTerminalByName(name) {
  return vscode.window.terminals.find((terminal) => terminal.name === name);
}

function getOrCreateTerminal(name) {
  const existing = findTerminalByName(name);
  if (existing) {
    return existing;
  }
  return vscode.window.createTerminal({ name });
}

function disposeTerminalByName(name) {
  const terminal = findTerminalByName(name);
  if (!terminal) {
    return false;
  }
  try {
    terminal.dispose();
    return true;
  } catch {
    return false;
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, Number(ms) || 0)));
}

async function focusTerminal(terminal) {
  try {
    if (vscode.window.activeTerminal?.name !== terminal.name) {
      terminal.show(false);
      await delay(50);
    }
  } catch {
    // ignore
  }
}

function parseSendArgs(args) {
  if (typeof args === "string") {
    return { text: args, submit: true };
  }

  if (args && typeof args === "object") {
    return {
      text: typeof args.text === "string" ? args.text : "",
      submit: typeof args.submit === "boolean" ? args.submit : true,
    };
  }

  return { text: "", submit: true };
}

function getSessionState(context) {
  return {
    startedCodex: Boolean(context.workspaceState.get(STATE_KEYS.startedCodex, false)),
    startedCopilot: Boolean(context.workspaceState.get(STATE_KEYS.startedCopilot, false)),
  };
}

async function startTerminalIfNeeded(context, terminal, stateKey, command, force = false) {
  const alreadyStarted = Boolean(context.workspaceState.get(stateKey, false));

  try {
    terminal.show(true);
  } catch {
    // ignore
  }

  if (alreadyStarted && !force) {
    return { started: false, reused: true };
  }

  terminal.sendText(String(command || ""), true);
  await context.workspaceState.update(stateKey, true);
  return { started: true, reused: false };
}

async function sendToTerminal(terminal, text, submit, submitDelayMs = 40) {
  const payload = String(text || "");
  await focusTerminal(terminal);

  if (!submit) {
    terminal.sendText(payload, false);
    return { submitted: false };
  }

  terminal.sendText(payload, false);
  await delay(submitDelayMs);
  terminal.sendText("\r", false);

  try {
    await focusTerminal(terminal);
    if (vscode.window.activeTerminal?.name === terminal.name) {
      await vscode.commands.executeCommand("workbench.action.terminal.sendSequence", {
        text: "\r",
      });
    }
  } catch {
    // ignore
  }

  return { submitted: true };
}

async function sendLiteralToTerminal(terminalName, args) {
  const terminal = findTerminalByName(terminalName);
  if (!terminal) {
    throw new Error(`Terminal '${terminalName}' not found. Start it first.`);
  }

  const payload = parseSendArgs(args);
  const text = String(payload.text || "");
  if (!text.trim() && !payload.submit) {
    throw new Error("Text to send is empty.");
  }

  const cfg = getConfig();
  await sendToTerminal(terminal, text, payload.submit, cfg.submitDelayMs);
  return {
    ok: true,
    terminalName,
    submit: payload.submit,
    textLength: text.length,
  };
}

async function promptAndSend(terminalName, title) {
  const text = await vscode.window.showInputBox({
    title,
    prompt: `Text will be sent to ${terminalName} via fallback sendText.`,
    placeHolder: "e.g. /status",
  });

  if (typeof text !== "string" || !text.trim()) {
    return undefined;
  }

  return sendLiteralToTerminal(terminalName, { text, submit: true });
}

async function startBackend(context, backendKind, force = true) {
  const cfg = getConfig();
  const stateKey = backendKind === "codex" ? STATE_KEYS.startedCodex : STATE_KEYS.startedCopilot;
  const terminalName = backendKind === "codex" ? cfg.codexTerminalName : cfg.copilotTerminalName;
  const command = backendKind === "codex" ? cfg.codexCommand : cfg.copilotCommand;
  const existing = findTerminalByName(terminalName);
  const terminal = existing || getOrCreateTerminal(terminalName);
  const result = await startTerminalIfNeeded(context, terminal, stateKey, command, force || !existing);
  logLine(JSON.stringify({ action: "start", backendKind, terminalName, command, result }, null, 2));
  return { terminalName, command, ...result };
}

async function restartBackend(context, backendKind) {
  const cfg = getConfig();
  const stateKey = backendKind === "codex" ? STATE_KEYS.startedCodex : STATE_KEYS.startedCopilot;
  const terminalName = backendKind === "codex" ? cfg.codexTerminalName : cfg.copilotTerminalName;
  disposeTerminalByName(terminalName);
  await context.workspaceState.update(stateKey, false);
  await delay(150);
  return startBackend(context, backendKind, true);
}

async function startAll(context) {
  const codex = await startBackend(context, "codex", true);
  const copilot = await startBackend(context, "copilot", true);
  return { codex, copilot };
}

function getLiveCaptureTarget(cfg, paths, terminalName) {
  if (!paths || !terminalName) {
    return undefined;
  }

  if (terminalName === cfg.codexTerminalName && cfg.alwaysCaptureCodex) {
    return {
      filePath: paths.liveFile,
      fileDisplay: paths.liveFileDisplay,
    };
  }

  if (terminalName === cfg.copilotTerminalName && cfg.alwaysCaptureCopilot) {
    return {
      filePath: paths.copilotLiveFile,
      fileDisplay: paths.copilotLiveFileDisplay,
    };
  }

  return undefined;
}

function appendRollingFile(filePath, buf, maxBytes) {
  fs.appendFileSync(filePath, buf);
  if (maxBytes <= 0) {
    return;
  }

  try {
    const stat = fs.statSync(filePath);
    if (stat.size <= maxBytes) {
      return;
    }
    const data = fs.readFileSync(filePath);
    const keepFrom = Math.max(0, data.length - maxBytes);
    fs.writeFileSync(filePath, data.subarray(keepFrom));
  } catch {
    // ignore
  }
}

function appendLiveCapture(cfg, terminal, data) {
  const paths = resolveCapturePaths(cfg);
  if (!paths) {
    return;
  }

  const target = getLiveCaptureTarget(cfg, paths, terminal?.name);
  if (!target) {
    return;
  }

  try {
    fs.mkdirSync(paths.dir, { recursive: true });
    const buf = Buffer.from(String(data || ""), "utf8");
    const maxBytes = Math.max(0, Number(cfg.captureMaxBytes) || 0);
    appendRollingFile(target.filePath, buf, maxBytes);
  } catch {
    // ignore
  }
}

function stripAnsi(value) {
  return String(value || "")
    .replace(/\x1b\[[0-9;?]*[ -/]*[@-~]/g, "")
    .replace(/\x1b\][^\x07]*(\x07|\x1b\\)/g, "")
    .replace(/\x1b\([^)]/g, "");
}

function readLastCaptureRaw(cfg) {
  const paths = resolveCapturePaths(cfg);
  if (!paths || !fs.existsSync(paths.lastFile)) {
    return "";
  }

  try {
    return fs.readFileSync(paths.lastFile, "utf8");
  } catch {
    return "";
  }
}

function analyzeCodexStatusCapture(raw) {
  const text = stripAnsi(String(raw || "")).replace(/\r/g, "\n");

  const hasStatusEcho = /(^|\n)\s*(›\s*)?\/status\b/i.test(text) || text.includes("/status");
  const hasContextLeft = /context left/i.test(text);
  const hasCodexSignal = /OpenAI Codex/i.test(text) || /\bTip:/i.test(text);
  const hasPastedOverlay = /\[Pasted Content\s+\d+\s+chars\]/i.test(text);

  return {
    ok: hasStatusEcho && (hasContextLeft || hasCodexSignal) && !hasPastedOverlay,
    hasStatusEcho,
    hasContextLeft,
    hasCodexSignal,
    hasPastedOverlay,
  };
}

function stopCapture(reason) {
  if (!captureState.active) {
    return;
  }

  captureState.active = false;
  if (captureState.stopTimer) {
    clearInterval(captureState.stopTimer);
  }
  captureState.stopTimer = undefined;
  if (typeof capturePromiseResolve === "function") {
    capturePromiseResolve(reason);
    capturePromiseResolve = undefined;
  }
}

function startCapture(cfg, terminalName) {
  const paths = resolveCapturePaths(cfg);
  if (!paths) {
    vscode.window.showErrorMessage("Workspace folder not found; cannot write capture file.");
    return undefined;
  }

  fs.mkdirSync(paths.dir, { recursive: true });
  fs.writeFileSync(paths.lastFile, "", "utf8");

  captureState = {
    active: true,
    terminalName,
    lastFile: paths.lastFile,
    startedAtMs: Date.now(),
    lastDataAtMs: Date.now(),
    bytesWritten: 0,
    stopTimer: undefined,
  };

  const maxMs = Math.max(0, Number(cfg.captureMaxSeconds) || 0) * 1000;
  const silenceMs = Math.max(0, Number(cfg.captureSilenceMs) || 0);
  captureState.stopTimer = setInterval(() => {
    if (!captureState.active) {
      return;
    }

    const now = Date.now();
    if (maxMs > 0 && now - captureState.startedAtMs >= maxMs) {
      stopCapture("timeout");
      return;
    }
    if (silenceMs > 0 && now - captureState.lastDataAtMs >= silenceMs) {
      stopCapture("silent");
    }
  }, 100);

  const capturePromise = new Promise((resolve) => {
    capturePromiseResolve = resolve;
  });

  return {
    captureFile: paths.lastFileDisplay,
    capturePromise,
  };
}

function appendCapture(cfg, terminal, data) {
  if (!captureState.active || !captureState.lastFile || !captureState.terminalName) {
    return;
  }
  if (terminal.name !== captureState.terminalName) {
    return;
  }

  const buf = Buffer.from(String(data || ""), "utf8");
  const maxBytes = Math.max(0, Number(cfg.captureMaxBytes) || 0);

  if (maxBytes > 0 && captureState.bytesWritten + buf.length > maxBytes) {
    const remaining = maxBytes - captureState.bytesWritten;
    if (remaining > 0) {
      fs.appendFileSync(captureState.lastFile, buf.subarray(0, remaining));
      captureState.bytesWritten += remaining;
    }
    stopCapture("size limit");
    return;
  }

  fs.appendFileSync(captureState.lastFile, buf);
  captureState.bytesWritten += buf.length;
  captureState.lastDataAtMs = Date.now();
}

function ensureCaptureSourceReady(cfg) {
  if (terminalDataWriteEventAvailable) {
    return true;
  }
  return shellReadState.attachedExecutionIdByTerminal.has(cfg.codexTerminalName);
}

async function captureWithCommand(text) {
  const cfg = getConfig();
  const terminal = findTerminalByName(cfg.codexTerminalName);
  if (!terminal) {
    vscode.window.showErrorMessage(
      `Terminal '${cfg.codexTerminalName}' not found. Start it first via fallback terminal runtime.`,
    );
    return { ok: false, error: "terminal_not_found" };
  }

  const captureResult = startCapture(cfg, cfg.codexTerminalName);
  if (!captureResult) {
    return { ok: false, error: "capture_start_failed" };
  }

  if (!ensureCaptureSourceReady(cfg)) {
    stopCapture("no capture source");
    vscode.window.showErrorMessage(
      "目前無法擷取輸出：Proposed API 不可用，且尚未掛上 shell integration fallback。",
    );
    return {
      ok: false,
      error: "no_capture_source",
      captureFile: captureResult.captureFile,
    };
  }

  await sendLiteralToTerminal(cfg.codexTerminalName, { text, submit: true });
  const stopReason = await captureResult.capturePromise;
  const rawCapture = readLastCaptureRaw(cfg);

  return {
    ok: true,
    captureFile: captureResult.captureFile,
    stopReason,
    rawCapture,
  };
}

function formatDiagnostics(context, cfg) {
  const paths = resolveCapturePaths(cfg);
  const root = getWorkspaceRootFsPath();
  const tokenInfo = root ? loadSendtextBridgeToken(root, false) : undefined;
  return {
    scaffold: false,
    activatedAt: new Date().toISOString(),
    commands: userFacingCommands,
    internalCommands,
    config: cfg,
    workspaceState: getSessionState(context),
    terminals: {
      codex: Boolean(findTerminalByName(cfg.codexTerminalName)),
      copilot: Boolean(findTerminalByName(cfg.copilotTerminalName)),
    },
    capture: {
      proposedApi: terminalDataWriteEventAvailable,
      shellReadAttachedTerminals: Array.from(shellReadState.attachedExecutionIdByTerminal.keys()),
      activeCapture: captureState.active
        ? {
            terminalName: captureState.terminalName,
            lastFile: captureState.lastFile,
            bytesWritten: captureState.bytesWritten,
          }
        : null,
      files: paths
        ? {
            lastFile: paths.lastFileDisplay,
            liveFile: paths.liveFileDisplay,
            copilotLiveFile: paths.copilotLiveFileDisplay,
            debugFile: paths.debugFileDisplay,
            bridgeAuditFile: paths.bridgeAuditFileDisplay,
          }
        : null,
    },
    bridge: {
      running: Boolean(sendtextBridgeServer),
      serverStartedAt: sendtextBridgeServerStartedAtIso || null,
      tokenConfigured: Boolean(tokenInfo?.token),
      tokenSource: tokenInfo?.source || null,
      tokenPath: tokenInfo?.path || (root ? resolveBridgeTokenPath(root) : null),
    },
  };
}

function sha256Hex(text) {
  return crypto.createHash("sha256").update(String(text || ""), "utf8").digest("hex");
}

function createRequestId() {
  try {
    return `req_${crypto.randomBytes(8).toString("hex")}`;
  } catch {
    return `req_${Date.now()}`;
  }
}

function normalizeIp(remoteAddress) {
  const value = String(remoteAddress || "");
  if (!value) {
    return "";
  }
  if (value === "::1") {
    return "127.0.0.1";
  }
  if (value.startsWith("::ffff:")) {
    return value.slice("::ffff:".length);
  }
  return value;
}

function jsonResponse(res, statusCode, obj) {
  try {
    res.statusCode = statusCode;
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.setHeader("Cache-Control", "no-store");
    res.end(JSON.stringify(obj));
  } catch {
    try {
      res.statusCode = 500;
      res.end('{"error":"internal_error"}');
    } catch {
      // ignore
    }
  }
}

function readJsonBody(req, maxBytes) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    const limit = Math.max(0, Number(maxBytes) || 0);

    req.on("data", (chunk) => {
      const buf = Buffer.isBuffer(chunk) ? chunk : Buffer.from(String(chunk || ""), "utf8");
      size += buf.length;
      if (limit > 0 && size > limit) {
        reject(new Error("request_too_large"));
        try {
          req.destroy();
        } catch {
          // ignore
        }
        return;
      }
      chunks.push(buf);
    });

    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8");
      if (!raw) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(raw));
      } catch {
        reject(new Error("invalid_json"));
      }
    });

    req.on("error", () => reject(new Error("request_error")));
  });
}

function ensureAllowedTerminalName(cfg, terminalKind) {
  const kind = String(terminalKind || "").trim();
  if (kind === "codex") {
    return cfg.codexTerminalName;
  }
  if (kind === "copilot") {
    return cfg.copilotTerminalName;
  }
  return undefined;
}

function extractBearerToken(req) {
  const auth = String(req.headers?.authorization || "").trim();
  if (auth.toLowerCase().startsWith("bearer ")) {
    return auth.slice("bearer ".length).trim();
  }
  const ivyToken = req.headers?.["x-ivy-token"];
  if (typeof ivyToken === "string" && ivyToken.trim()) {
    return ivyToken.trim();
  }
  return undefined;
}

function appendSendtextBridgeAuditEvent(cfg, event) {
  const paths = resolveCapturePaths(cfg);
  if (!paths) {
    return;
  }

  try {
    fs.mkdirSync(paths.dir, { recursive: true });
    fs.appendFileSync(paths.bridgeAuditFile, `${JSON.stringify(event)}\n`, "utf8");
  } catch {
    // ignore
  }
}

function loadSendtextBridgeToken(rootAbs, createIfMissing) {
  const envToken = process.env.IVY_SENDTEXT_BRIDGE_TOKEN;
  if (envToken && String(envToken).trim()) {
    return {
      token: String(envToken).trim(),
      source: "env",
      path: resolveBridgeTokenPath(rootAbs),
      created: false,
    };
  }

  const tokenPath = resolveBridgeTokenPath(rootAbs);
  try {
    if (fs.existsSync(tokenPath)) {
      const token = String(fs.readFileSync(tokenPath, "utf8") || "").trim();
      if (token) {
        return {
          token,
          source: "file",
          path: tokenPath,
          created: false,
        };
      }
    }
  } catch {
    // ignore
  }

  if (!createIfMissing) {
    return undefined;
  }

  const token = crypto.randomBytes(24).toString("hex");
  fs.mkdirSync(path.dirname(tokenPath), { recursive: true });
  fs.writeFileSync(tokenPath, `${token}\n`, { encoding: "utf8", mode: 0o600 });
  try {
    fs.chmodSync(tokenPath, 0o600);
  } catch {
    // ignore
  }
  return {
    token,
    source: "file",
    path: tokenPath,
    created: true,
  };
}

function rateLimiterCreate(cfg) {
  const limitPerSec = Math.max(0, Number(cfg.bridgeRateLimit) || 0);
  const burst = Math.max(0, Number(cfg.bridgeRateBurst) || 0);
  const buckets = new Map();

  function take(ip) {
    if (limitPerSec <= 0 || burst <= 0) {
      return { ok: true };
    }

    const now = Date.now();
    const key = ip || "";
    const previous = buckets.get(key) || { tokens: burst, lastMs: now };
    const elapsed = Math.max(0, now - previous.lastMs);
    const refill = (elapsed / 1000) * limitPerSec;
    const tokens = Math.min(burst, previous.tokens + refill);

    if (tokens < 1) {
      buckets.set(key, { tokens, lastMs: now });
      return { ok: false, retryAfter: Math.max(1, Math.ceil((1 - tokens) / limitPerSec)) };
    }

    buckets.set(key, { tokens: tokens - 1, lastMs: now });
    return { ok: true };
  }

  return { take };
}

async function sendInstructionViaBridge(context, cfg, body) {
  const terminalKind = String(body?.terminalKind || "").trim();
  const text = String(body?.text || "");
  const submit = Boolean(body?.submit);
  const terminalName = ensureAllowedTerminalName(cfg, terminalKind);

  if (!terminalName) {
    return { ok: false, error: "invalid_terminal_kind" };
  }

  const textBytes = Buffer.byteLength(text, "utf8");
  const maxPayload = Math.max(0, Number(cfg.bridgeMaxPayloadBytes) || 0);
  if (maxPayload > 0 && textBytes > maxPayload) {
    return {
      ok: false,
      error: "payload_too_large",
      textBytes,
      maxBytes: maxPayload,
    };
  }

  const isStarted = terminalKind === "codex"
    ? context.workspaceState.get(STATE_KEYS.startedCodex, false)
    : context.workspaceState.get(STATE_KEYS.startedCopilot, false);
  if (!findTerminalByName(terminalName) && !isStarted) {
    return {
      ok: false,
      error: "terminal_not_found",
      terminalName,
    };
  }

  await sendLiteralToTerminal(terminalName, { text, submit });
  return {
    ok: true,
    terminalKind,
    terminalName,
    submit,
    textBytes,
    payloadSha256: sha256Hex(text),
    mode: "single",
  };
}

function startSendtextBridgeServer(context) {
  const cfg = getConfig();
  const root = getWorkspaceRootFsPath();
  if (!root) {
    throw new Error("Workspace folder not found; cannot start fallback bridge.");
  }
  if (sendtextBridgeServer) {
    return {
      running: true,
      host: "127.0.0.1",
      port: Math.max(1, Math.min(65535, Number(cfg.bridgePort) || 8765)),
      token: loadSendtextBridgeToken(root, false),
      startedAt: sendtextBridgeServerStartedAtIso,
    };
  }

  const tokenInfo = loadSendtextBridgeToken(root, true);
  const limiter = rateLimiterCreate(cfg);
  const host = "127.0.0.1";
  const port = Math.max(1, Math.min(65535, Number(cfg.bridgePort) || 8765));
  sendtextBridgeServerStartedAtIso = new Date().toISOString();

  const server = http.createServer(async (req, res) => {
    const method = String(req.method || "GET").toUpperCase();
    const url = String(req.url || "/");
    const endpoint = url.split("?")[0];
    const ip = normalizeIp(req.socket?.remoteAddress);
    const requestId = createRequestId();
    const tokenConfigured = loadSendtextBridgeToken(root, false);
    const tokenHash = tokenConfigured?.token ? sha256Hex(tokenConfigured.token) : "";
    const providedToken = extractBearerToken(req);
    const authed = Boolean(tokenConfigured?.token) && Boolean(providedToken) && providedToken === tokenConfigured.token;

    const rate = limiter.take(ip);
    if (!rate.ok) {
      appendSendtextBridgeAuditEvent(cfg, {
        ts: new Date().toISOString(),
        endpoint,
        result: "rate_limited",
        requestId,
        tokenHash,
        ip,
        retryAfter: rate.retryAfter,
      });
      jsonResponse(res, 429, { error: "rate_limited", retryAfter: rate.retryAfter, requestId });
      return;
    }

    if (method === "GET" && endpoint === "/healthz") {
      jsonResponse(res, 200, {
        status: "ok",
        ts: new Date().toISOString(),
        serverStartedAt: sendtextBridgeServerStartedAtIso,
      });
      return;
    }

    if (method === "POST" && endpoint === "/send") {
      if (!tokenConfigured?.token) {
        appendSendtextBridgeAuditEvent(cfg, {
          ts: new Date().toISOString(),
          endpoint,
          result: "rejected",
          error: "token_not_configured",
          requestId,
          tokenHash,
          ip,
        });
        jsonResponse(res, 503, { error: "token_not_configured", requestId });
        return;
      }

      if (!authed) {
        appendSendtextBridgeAuditEvent(cfg, {
          ts: new Date().toISOString(),
          endpoint,
          result: "rejected",
          error: "unauthorized",
          requestId,
          tokenHash,
          ip,
        });
        jsonResponse(res, 401, { error: "unauthorized", requestId });
        return;
      }

      let body;
      try {
        body = await readJsonBody(req, cfg.bridgeMaxRequestBytes);
      } catch (error) {
        const code = String(error?.message || "bad_request");
        jsonResponse(res, code === "request_too_large" ? 413 : 400, {
          error: code,
          requestId,
        });
        return;
      }

      const sendResult = await sendInstructionViaBridge(context, cfg, body);
      appendSendtextBridgeAuditEvent(cfg, {
        ts: new Date().toISOString(),
        endpoint,
        result: sendResult.ok ? "success" : "error",
        requestId,
        terminalKind: sendResult.terminalKind || String(body?.terminalKind || ""),
        submit: Boolean(body?.submit),
        textBytes: sendResult.textBytes || 0,
        payloadSha256: sendResult.payloadSha256 || "",
        tokenHash,
        ip,
        error: sendResult.ok ? undefined : sendResult.error,
      });

      if (!sendResult.ok) {
        jsonResponse(res, 400, { error: sendResult.error, requestId });
        return;
      }

      jsonResponse(res, 200, {
        status: "sent",
        terminalKind: sendResult.terminalKind,
        textBytes: sendResult.textBytes,
        requestId,
      });
      return;
    }

    jsonResponse(res, 404, { error: "not_found", requestId });
  });

  server.on("error", (error) => {
    logLine(`[bridge] server error: ${String(error || "")}`);
  });

  server.listen(port, host, () => {
    logLine(`[bridge] Fallback bridge listening on http://${host}:${port}`);
  });
  sendtextBridgeServer = server;

  return {
    running: true,
    host,
    port,
    token: tokenInfo,
    startedAt: sendtextBridgeServerStartedAtIso,
  };
}

async function stopSendtextBridgeServer() {
  const server = sendtextBridgeServer;
  sendtextBridgeServer = undefined;
  if (!server) {
    return { running: false };
  }

  await new Promise((resolve) => {
    server.close(() => resolve());
  });
  logLine("[bridge] fallback bridge stopped");
  return { running: false };
}

function showNotImplemented(commandId, args) {
  const payload = {
    commandId,
    args: args ?? null,
    config: getConfig(),
  };
  logLine(JSON.stringify(payload, null, 2));
  return vscode.window.showWarningMessage(`Fallback scaffold only: ${commandId} is not implemented yet.`);
}

function activate(context) {
  outputChannel = vscode.window.createOutputChannel("IvyHouse Terminal Fallback");
  context.subscriptions.push(outputChannel);

  appendDebugEvent(getConfig(), {
    type: "activate",
    vscodeVersion: vscode.version,
  });

  try {
    if (vscode.window.onDidWriteTerminalData) {
      terminalDataWriteEventAvailable = true;
      context.subscriptions.push(
        vscode.window.onDidWriteTerminalData((event) => {
          const cfg = getConfig();
          appendLiveCapture(cfg, event.terminal, event.data);
          appendCapture(cfg, event.terminal, event.data);
        }),
      );
    }
  } catch (error) {
    terminalDataWriteEventAvailable = false;
    logLine(`[capture] proposed API unavailable: ${String(error || "")}`);
  }

  appendDebugEvent(getConfig(), {
    type: "proposed_api",
    onDidWriteTerminalData: terminalDataWriteEventAvailable,
  });

  try {
    if (vscode.window.onDidStartTerminalShellExecution) {
      context.subscriptions.push(
        vscode.window.onDidStartTerminalShellExecution((event) => {
          try {
            const cfg = getConfig();
            const terminalName = event?.terminal?.name;
            if (!terminalName) {
              return;
            }

            const isCodexTerminal = terminalName === cfg.codexTerminalName;
            const isCopilotTerminal = terminalName === cfg.copilotTerminalName;
            if (!isCodexTerminal && !isCopilotTerminal) {
              return;
            }

            const commandLine = typeof event.execution?.commandLine?.value === "string"
              ? event.execution.commandLine.value
              : "";

            if (typeof event.execution?.read !== "function") {
              appendDebugEvent(cfg, {
                type: "shell_execution_start",
                terminalName,
                commandLine,
                hasRead: false,
              });
              return;
            }

            appendDebugEvent(cfg, {
              type: "shell_execution_start",
              terminalName,
              commandLine,
              hasRead: true,
            });

            const currentId = shellReadState.attachedExecutionIdByTerminal.get(terminalName) || 0;
            const execId = currentId + 1;
            shellReadState.attachedExecutionIdByTerminal.set(terminalName, execId);
            shellReadState.lastAttachedTerminalName = terminalName;

            let sawData = false;

            (async () => {
              try {
                const stream = event.execution.read();
                for await (const data of stream) {
                  if (shellReadState.attachedExecutionIdByTerminal.get(terminalName) !== execId) {
                    break;
                  }
                  const cfgNow = getConfig();
                  if (!sawData) {
                    sawData = true;
                    let bytes = 0;
                    try {
                      if (Buffer.isBuffer(data)) {
                        bytes = data.length;
                      } else if (data instanceof Uint8Array) {
                        bytes = data.byteLength;
                      } else {
                        bytes = Buffer.byteLength(String(data || ""), "utf8");
                      }
                    } catch {
                      bytes = 0;
                    }
                    appendDebugEvent(cfgNow, {
                      type: "shell_execution_first_data",
                      terminalName,
                      execId,
                      bytes,
                    });
                  }
                  appendLiveCapture(cfgNow, event.terminal, data);
                  appendCapture(cfgNow, event.terminal, data);
                }
              } catch (error) {
                appendDebugEvent(getConfig(), {
                  type: "shell_execution_error",
                  terminalName,
                  execId,
                  error: String(error || ""),
                });
              } finally {
                appendDebugEvent(getConfig(), {
                  type: "shell_execution_end",
                  terminalName,
                  execId,
                  sawData,
                });
              }
            })();
          } catch (error) {
            logLine(`[capture] shell execution hook failed: ${String(error || "")}`);
          }
        }),
      );
    }
  } catch (error) {
    logLine(`[capture] shell integration unavailable: ${String(error || "")}`);
  }

  for (const commandId of userFacingCommands) {
    context.subscriptions.push(
      vscode.commands.registerCommand(commandId, async (args) => {
        if (commandId === "ivyhouseTerminalFallback.showDiagnostics") {
          const diagnostics = formatDiagnostics(context, getConfig());
          logLine(JSON.stringify(diagnostics, null, 2));
          outputChannel.show(true);
          return diagnostics;
        }
        if (commandId === "ivyhouseTerminalFallback.startCodex") {
          return startBackend(context, "codex", true);
        }
        if (commandId === "ivyhouseTerminalFallback.restartCodex") {
          return restartBackend(context, "codex");
        }
        if (commandId === "ivyhouseTerminalFallback.startCopilot") {
          return startBackend(context, "copilot", true);
        }
        if (commandId === "ivyhouseTerminalFallback.restartCopilot") {
          return restartBackend(context, "copilot");
        }
        if (commandId === "ivyhouseTerminalFallback.startAll") {
          return startAll(context);
        }
        if (commandId === "ivyhouseTerminalFallback.sendToCodex") {
          return promptAndSend(getConfig().codexTerminalName, "Send text to Codex fallback terminal");
        }
        if (commandId === "ivyhouseTerminalFallback.sendToCopilot") {
          return promptAndSend(getConfig().copilotTerminalName, "Send text to Copilot fallback terminal");
        }
        if (commandId === "ivyhouseTerminalFallback.captureCodexOutput") {
          const text = await vscode.window.showInputBox({
            title: "Capture output from Codex fallback terminal",
            prompt: "Command will be sent through the fallback terminal runtime and output will be captured.",
            value: "/status",
          });
          if (typeof text !== "string" || !text.trim()) {
            return undefined;
          }
          return captureWithCommand(text);
        }
        if (commandId === "ivyhouseTerminalFallback.autoCaptureCodexStatus") {
          return captureWithCommand("/status");
        }
        if (commandId === "ivyhouseTerminalFallback.restartAndCaptureCodexStatus") {
          await restartBackend(context, "codex");
          await delay(5000);
          return captureWithCommand("/status");
        }
        if (commandId === "ivyhouseTerminalFallback.verifyCodexStatusInjection") {
          await restartBackend(context, "codex");
          await delay(5000);
          const capture = await captureWithCommand("/status");
          if (!capture || !capture.ok) {
            vscode.window.showErrorMessage(`Codex /status fallback 驗證失敗：${capture?.error || "unknown_error"}`);
            return capture;
          }

          const analysis = analyzeCodexStatusCapture(capture.rawCapture || "");
          const summary = [
            `status=${analysis.hasStatusEcho ? "Y" : "N"}`,
            `context=${analysis.hasContextLeft ? "Y" : "N"}`,
            `codexSignal=${analysis.hasCodexSignal ? "Y" : "N"}`,
            `overlay=${analysis.hasPastedOverlay ? "Y" : "N"}`,
            `stop=${capture.stopReason || "unknown"}`,
          ].join(" | ");

          if (analysis.ok) {
            vscode.window.showInformationMessage(`✅ Codex /status fallback 驗證通過 (${summary})`);
          } else {
            vscode.window.showWarningMessage(`⚠️ Codex /status fallback 驗證未通過 (${summary})`);
          }
          return {
            ...capture,
            analysis,
            summary,
          };
        }
        if (commandId === "ivyhouseTerminalFallback.resetSessionState") {
          await context.workspaceState.update(STATE_KEYS.startedCodex, false);
          await context.workspaceState.update(STATE_KEYS.startedCopilot, false);
          stopCapture("reset_session_state");
          vscode.window.showInformationMessage("IvyHouse Terminal Fallback session state reset.");
          return getSessionState(context);
        }
        return showNotImplemented(commandId, args);
      }),
    );
  }

  for (const commandId of internalCommands) {
    context.subscriptions.push(
      vscode.commands.registerCommand(commandId, async (args) => {
        if (commandId === "ivyhouseTerminalFallback.sendLiteral") {
          const terminalKind = args?.terminalKind;
          if (terminalKind !== "codex" && terminalKind !== "copilot") {
            throw new Error("sendLiteral requires terminalKind=codex|copilot.");
          }
          const terminalName = terminalKind === "codex" ? getConfig().codexTerminalName : getConfig().copilotTerminalName;
          return sendLiteralToTerminal(terminalName, args);
        }
        if (commandId === "ivyhouseTerminalFallback.sendLiteralToCodex") {
          return sendLiteralToTerminal(getConfig().codexTerminalName, args);
        }
        if (commandId === "ivyhouseTerminalFallback.sendLiteralToCopilot") {
          return sendLiteralToTerminal(getConfig().copilotTerminalName, args);
        }
        if (commandId === "ivyhouseTerminalFallback.startBridge") {
          return startSendtextBridgeServer(context);
        }
        if (commandId === "ivyhouseTerminalFallback.stopBridge") {
          return stopSendtextBridgeServer();
        }
        return showNotImplemented(commandId, args);
      }),
    );
  }
}

function deactivate() {
  stopCapture("deactivate");
  if (sendtextBridgeServer) {
    try {
      sendtextBridgeServer.close();
    } catch {
      // ignore
    }
    sendtextBridgeServer = undefined;
  }
  if (outputChannel) {
    outputChannel.dispose();
  }
}

module.exports = {
  activate,
  deactivate,
};
