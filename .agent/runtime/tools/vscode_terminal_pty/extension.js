/* 檔案用途：提供 Codex/Copilot 雙 backend 的 PTY-native VS Code extension runtime。 */
/* eslint-disable no-console */
const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");

const BRIDGE_SCRIPT = path.join(__dirname, "codex_pty_bridge.py");

const BACKEND_KINDS = {
  CODEX: "codex",
  COPILOT: "copilot",
};

const RECOVERY_STATES = {
  NORMAL: "normal",
  RETRYABLE: "retryable",
  REBUILDABLE: "rebuildable",
  PROMPTING_FALLBACK: "prompting-fallback",
  FALLBACK_ACTIVE: "fallback-active",
  FALLBACK_DECLINED: "fallback-declined",
};

const FALLBACK_DECISIONS = {
  NONE: "none",
  PENDING: "pending",
  ACCEPTED: "accepted",
  DECLINED: "declined",
};

const ERROR_CODES = {
  PTY_SEND_TIMEOUT: "PTY_SEND_TIMEOUT",
  PTY_SUBMIT_TIMEOUT: "PTY_SUBMIT_TIMEOUT",
  PTY_VERIFY_TIMEOUT: "PTY_VERIFY_TIMEOUT",
  PTY_WRITE_FAILED: "PTY_WRITE_FAILED",
  PTY_CHILD_EXITED: "PTY_CHILD_EXITED",
  PTY_PIPE_BROKEN: "PTY_PIPE_BROKEN",
  PTY_TERMINAL_DISPOSED: "PTY_TERMINAL_DISPOSED",
  PTY_SESSION_DESYNC: "PTY_SESSION_DESYNC",
  PTY_RETRY_EXHAUSTED: "PTY_RETRY_EXHAUSTED",
  PTY_REBUILD_FAILED: "PTY_REBUILD_FAILED",
  PTY_VERIFY_AFTER_REBUILD_FAILED: "PTY_VERIFY_AFTER_REBUILD_FAILED",
  PTY_FALLBACK_REQUIRED: "PTY_FALLBACK_REQUIRED",
  PTY_FALLBACK_HANDOFF_FAILED: "PTY_FALLBACK_HANDOFF_FAILED",
  PTY_FALLBACK_DECLINED: "PTY_FALLBACK_DECLINED",
  PTY_MANUAL_INTERVENTION_REQUIRED: "PTY_MANUAL_INTERVENTION_REQUIRED",
};

const SESSION_LEVEL_ERRORS = new Set([
  ERROR_CODES.PTY_CHILD_EXITED,
  ERROR_CODES.PTY_PIPE_BROKEN,
  ERROR_CODES.PTY_TERMINAL_DISPOSED,
  ERROR_CODES.PTY_SESSION_DESYNC,
]);

const CSI_U_ENTER_PRESS = "\x1b[13u";
const CSI_U_ENTER_RELEASE = "\x1b[13;1:3u";
const CTRL_S = "\x13";

let outputChannel;
let runtimeStore;

function makeError(code, message) {
  const error = new Error(message);
  error.code = code;
  return error;
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, Number(ms) || 0)));
}

function makeRequestId() {
  runtimeStore.requestCounter += 1;
  return `req-${Date.now()}-${runtimeStore.requestCounter}`;
}

function encodeCsiUKeyPress(codePoint) {
  return `\x1b[${codePoint}u`;
}

function encodeCsiUKeyRelease(codePoint) {
  return `\x1b[${codePoint};1:3u`;
}

function stripAnsi(value) {
  return String(value || "")
    .replace(/\x1b\[[0-9;?]*[ -/]*[@-~]/g, "")
    .replace(/\x1b\][^\x07]*(\x07|\x1b\\)/g, "")
    .replace(/\x1b\([^)]/g, "");
}

function normalizeOutputText(value) {
  return stripAnsi(String(value || "")).replace(/\r/g, "\n").toLowerCase();
}

function toSemanticText(value) {
  return stripAnsi(String(value || ""))
    .replace(/\r/g, "\n")
    .replace(/[\u2500-\u257f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function hasMeaningfulProgressOutput(value) {
  const text = normalizeOutputText(value);
  if (!text.trim()) return false;
  if (/(working|thinking|analy|context left|esc to interrupt|model:|openai codex|github copilot)/i.test(text)) {
    return true;
  }
  return text.trim().length >= 3;
}

function toDebugPreview(value, limit = 240) {
  const text = typeof value === "string" ? value : Buffer.from(value || "").toString("utf8");
  return JSON.stringify(text.slice(0, Math.max(0, Number(limit) || 0)));
}

function getWorkspaceRootFsPath() {
  return vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath || process.cwd();
}

function resolveCaptureDir() {
  return path.join(getWorkspaceRootFsPath(), getConfig().captureDir);
}

function resolveCapturePath(fileName) {
  return path.join(resolveCaptureDir(), fileName);
}

function ensureCaptureDir() {
  const captureDir = resolveCaptureDir();
  fs.mkdirSync(captureDir, { recursive: true });
  return captureDir;
}

function appendOutputLine(line) {
  if (!outputChannel) return;
  outputChannel.appendLine(line);
}

function resolveArtifactNames(kind) {
  const profile = getProfile(kind);
  return {
    live: `${profile.artifactPrefix}_live.txt`,
    debug: `${profile.artifactPrefix}_debug.jsonl`,
  };
}

function makeArtifactRotationTimestamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function resolveRotatedCapturePath(kind, fileType, timestamp) {
  const currentName = resolveArtifactNames(kind)[fileType];
  const extension = path.extname(currentName);
  const baseName = currentName.slice(0, currentName.length - extension.length);
  return resolveCapturePath(`${baseName}.${timestamp}${extension}`);
}

function touchFile(filePath) {
  const handle = fs.openSync(filePath, "a");
  fs.closeSync(handle);
}

function rotateArtifactFile(currentPath, rotatedPath) {
  if (!fs.existsSync(currentPath)) return false;
  const stat = fs.statSync(currentPath);
  if (!stat.isFile() || stat.size === 0) return false;
  fs.renameSync(currentPath, rotatedPath);
  return true;
}

function listRotatedArtifactPaths(kind, fileType) {
  const currentName = resolveArtifactNames(kind)[fileType];
  const extension = path.extname(currentName);
  const baseName = currentName.slice(0, currentName.length - extension.length);
  return fs
    .readdirSync(resolveCaptureDir(), { withFileTypes: true })
    .filter(
      (entry) =>
        entry.isFile() &&
        entry.name !== currentName &&
        entry.name.startsWith(`${baseName}.`) &&
        entry.name.endsWith(extension),
    )
    .map((entry) => resolveCapturePath(entry.name));
}

function pruneRotatedArtifacts(kind, fileType, maxHistory) {
  if (maxHistory < 0) return;
  const rotatedPaths = listRotatedArtifactPaths(kind, fileType)
    .map((filePath) => ({
      filePath,
      mtimeMs: fs.statSync(filePath).mtimeMs,
    }))
    .sort((left, right) => right.mtimeMs - left.mtimeMs);

  for (const entry of rotatedPaths.slice(maxHistory)) {
    fs.unlinkSync(entry.filePath);
  }
}

function touchCurrentArtifacts(kind) {
  ensureCaptureDir();
  const artifacts = resolveArtifactNames(kind);
  touchFile(resolveCapturePath(artifacts.debug));
  touchFile(resolveCapturePath(artifacts.live));
}

function shouldRotateArtifacts(reason, config) {
  if (reason === "start") return config.rotateArtifactsOnStart;
  if (reason === "restart") return config.rotateArtifactsOnRestart;
  if (reason === "new-workflow") return config.rotateArtifactsOnNewWorkflow;
  return true;
}

function rotateCurrentArtifacts(kind, reason) {
  const config = getConfig();
  if (!shouldRotateArtifacts(reason, config)) {
    touchCurrentArtifacts(kind);
    return { rotatedFiles: [], skipped: true };
  }

  ensureCaptureDir();
  const timestamp = makeArtifactRotationTimestamp();
  const rotatedFiles = [];

  for (const fileType of ["debug", "live"]) {
    const currentPath = resolveCapturePath(resolveArtifactNames(kind)[fileType]);
    const rotatedPath = resolveRotatedCapturePath(kind, fileType, timestamp);
    if (rotateArtifactFile(currentPath, rotatedPath)) {
      rotatedFiles.push(path.basename(rotatedPath));
    }
    pruneRotatedArtifacts(kind, fileType, config.rotationMaxHistory);
  }

  touchCurrentArtifacts(kind);
  emitEvent("pty.artifacts.rotated", {
    kind,
    reason,
    rotatedFiles,
    timestamp,
  });
  return { rotatedFiles, skipped: false, timestamp };
}

function appendLiveLog(kind, text) {
  const fileName = resolveArtifactNames(kind).live;
  try {
    ensureCaptureDir();
    fs.appendFileSync(resolveCapturePath(fileName), String(text || ""), "utf8");
  } catch {
    // ignore
  }
}

function appendDebugEvent(kind, event) {
  const fileName = resolveArtifactNames(kind).debug;
  try {
    ensureCaptureDir();
    fs.appendFileSync(
      resolveCapturePath(fileName),
      `${JSON.stringify({ ts: new Date().toISOString(), kind, ...event })}\n`,
      "utf8",
    );
  } catch {
    // ignore
  }
}

function emitEvent(type, payload) {
  const kind = payload?.kind || BACKEND_KINDS.CODEX;
  appendDebugEvent(kind, { type, ...payload });
}

function normalizeBackendKind(kind) {
  if (!kind || kind === BACKEND_KINDS.CODEX) return BACKEND_KINDS.CODEX;
  if (kind === BACKEND_KINDS.COPILOT) return BACKEND_KINDS.COPILOT;
  throw makeError(ERROR_CODES.PTY_SESSION_DESYNC, `Unknown backend kind: ${String(kind)}`);
}

function resolvePythonExecutable() {
  const workspacePython = path.join(getWorkspaceRootFsPath(), ".venv", "bin", "python");
  if (fs.existsSync(workspacePython)) return workspacePython;
  if (process.env.PYTHON && String(process.env.PYTHON).trim()) return String(process.env.PYTHON).trim();
  return "python3";
}

function normalizeTerminalDimensions(dimensions) {
  const columns = Math.max(40, Number(dimensions?.columns) || 160);
  const rows = Math.max(12, Number(dimensions?.rows) || 40);
  return { columns, rows };
}

function encodePtyControlMessage(message) {
  return `${JSON.stringify(message)}\n`;
}

function findTerminalByName(name) {
  return vscode.window.terminals.find((terminal) => terminal.name === name);
}

function parseSendArgs(args, defaultSubmit = false) {
  if (typeof args === "string") {
    return { text: args, submit: defaultSubmit };
  }

  if (args && typeof args === "object") {
    return {
      text: typeof args.text === "string" ? args.text : "",
      submit: typeof args.submit === "boolean" ? args.submit : defaultSubmit,
    };
  }

  return { text: "", submit: defaultSubmit };
}

function getCommandSettingKey(kind) {
  if (kind === BACKEND_KINDS.COPILOT) return "copilotCommand";
  return "codexCommand";
}

function createSessionState(kind) {
  return {
    kind,
    sessionId: null,
    terminal: null,
    proc: null,
    bridgeControl: null,
    writeInput: null,
    csiUKeyboardProtocolEnabled: false,
    startupReady: false,
    startupReadyDeadlineAt: 0,
    startupSignals: {
      headerSeen: false,
      modelResolvedSeen: false,
      statusSeen: false,
      promptSeen: false,
    },
    recentOutput: "",
    outputWaiters: new Map(),
    lastOutputAt: 0,
    sessionCloseBarrier: null,
    recoveryState: RECOVERY_STATES.NORMAL,
    lastErrorCode: null,
    lastErrorSummary: null,
    lastFailedCommand: null,
    retryCount: 0,
    maxRetryCount: 1,
    fallbackDecision: FALLBACK_DECISIONS.NONE,
    fallbackOfferedAt: null,
    lastFallbackHandoff: null,
    lastVerify: null,
    lastSmokeTest: null,
    lastAction: null,
  };
}

function createInitialRuntimeStore() {
  return {
    requestCounter: 0,
    sessionsByKind: {
      [BACKEND_KINDS.CODEX]: createSessionState(BACKEND_KINDS.CODEX),
      [BACKEND_KINDS.COPILOT]: createSessionState(BACKEND_KINDS.COPILOT),
    },
  };
}

function getSession(kind) {
  return runtimeStore.sessionsByKind[normalizeBackendKind(kind)];
}

function isActiveSession(session, sessionId) {
  return session.sessionId === sessionId;
}

function getConfig() {
  const cfg = vscode.workspace.getConfiguration("ivyhouseTerminalPty");
  const legacyAutoStart = cfg.get("autoStart", false);
  const legacyCodexTerminalName = cfg.get("terminalName", "Codex PTY");
  const legacyCodexVerifyPrompt = cfg.get("verifyPrompt", "reply with exactly pty-verify-ok");
  const legacyCodexVerifyExpected = cfg.get("verifyExpected", "pty-verify-ok");
  const smokeIterationCount = Math.max(1, Number(cfg.get("smokeIterationCount", 3)) || 3);
  const maxRetryCount = Math.max(0, Number(cfg.get("maxRetryCount", 1)) || 0);
  const startupReadyDebounceMs = Math.max(
    0,
    Number(cfg.get("startupReadyDebounceMs", cfg.get("startupSettledSilenceMs", 500))) || 0,
  );

  return {
    captureDir: cfg.get("captureDir", ".service/terminal_capture"),
    rotateArtifactsOnStart: cfg.get("rotateArtifactsOnStart", true),
    rotateArtifactsOnRestart: cfg.get("rotateArtifactsOnRestart", true),
    rotateArtifactsOnNewWorkflow: cfg.get("rotateArtifactsOnNewWorkflow", true),
    rotationMaxHistory: Math.max(0, Number(cfg.get("rotationMaxHistory", 5)) || 5),
    verifyTimeoutMs: Math.max(1000, Number(cfg.get("verifyTimeoutMs", 12000)) || 12000),
    verifyMaxTimeoutMs: Math.max(1000, Number(cfg.get("verifyMaxTimeoutMs", 45000)) || 45000),
    startupTimeoutMs: Math.max(1000, Number(cfg.get("startupTimeoutMs", 8000)) || 8000),
    startupReadyDebounceMs,
    smokeIterationCount,
    maxRetryCount,
    profiles: {
      [BACKEND_KINDS.CODEX]: {
        kind: BACKEND_KINDS.CODEX,
        command: cfg.get("codexCommand", "codex"),
        terminalName: cfg.get("codexTerminalName", legacyCodexTerminalName),
        autoStart: cfg.get("autoStartCodex", legacyAutoStart),
        artifactPrefix: "codex_pty",
        verifySpec: {
          prompt: cfg.get("codexVerifyPrompt", legacyCodexVerifyPrompt),
          expected: cfg.get("codexVerifyExpected", legacyCodexVerifyExpected),
        },
        smokeSpec: [
          { label: "smoke-ping", prompt: "reply with exactly pong", expected: "pong" },
          { label: "smoke-ok", prompt: "reply with exactly smoke-ok", expected: "smoke-ok" },
        ],
        submitPolicy: {
          settleDelayMs: 140,
          settleMinTextLength: 3,
          settleReason: "avoid paste-burst Enter suppression",
        },
        closePolicy: {
          forceKillDelayMs: Math.max(0, Number(cfg.get("codexCloseForceKillDelayMs", 500)) || 500),
        },
        startup: {
          requireCsiU: true,
          headerPattern: /open\s*ai\s*codex|codex/i,
          modelPattern: /model:|gpt-[0-9.]+|high\s*·\s*[0-9]+%\s*left/i,
          statusPattern: /context\s*left|esc\s*to\s*interrupt|%\s*left|\/review|\/workspaces\//i,
          promptPattern: /[›>]\s*[a-z/]/i,
        },
        ux: {
          label: "Codex PTY",
          sendTitle: "Send text to Codex PTY",
          sendPrompt: "Text will be sent through the PTY-native Codex session.",
          verifySuccess: (expected) => `Codex PTY verify succeeded: '${expected}'.`,
          smokeSuccess: (iterations) =>
            `Codex PTY smoke test passed ${iterations} iteration${iterations === 1 ? "" : "s"}: pong + smoke-ok.`,
          fallbackPrompt: (errorCode) => `Codex PTY rebuild failed (${errorCode}). Enable fallback tool?`,
        },
      },
      [BACKEND_KINDS.COPILOT]: {
        kind: BACKEND_KINDS.COPILOT,
        command: cfg.get("copilotCommand", "copilot"),
        terminalName: cfg.get("copilotTerminalName", "Copilot PTY"),
        autoStart: cfg.get("autoStartCopilot", false),
        artifactPrefix: "copilot_pty",
        verifySpec: {
          prompt: cfg.get("copilotVerifyPrompt", "reply with exactly pty-verify-ok"),
          expected: cfg.get("copilotVerifyExpected", "pty-verify-ok"),
        },
        smokeSpec: [
          { label: "smoke-ping", prompt: "reply with exactly pong", expected: "pong" },
          { label: "smoke-ok", prompt: "reply with exactly smoke-ok", expected: "smoke-ok" },
        ],
        submitPolicy: {
          settleDelayMs: 140,
          settleMinTextLength: 3,
          settleReason: "avoid paste-burst Enter suppression",
        },
        inputPolicy: {
          textMode: "direct-text",
            submitMode: "carriage-return",
        },
        closePolicy: {
          forceKillDelayMs: Math.max(0, Number(cfg.get("copilotCloseForceKillDelayMs", 1500)) || 1500),
        },
        startup: {
          requireCsiU: true,
          freshPromptDelayMs: 1500,
          composerInputGate: {
            enabled: true,
            attempts: Math.max(1, Number(cfg.get("copilotComposerInputGateAttempts", 4)) || 4),
            timeoutMs: Math.max(250, Number(cfg.get("copilotComposerInputGateTimeoutMs", 1800)) || 1800),
            retryDelayMs: Math.max(0, Number(cfg.get("copilotComposerInputGateRetryDelayMs", 500)) || 500),
            eraseDelayMs: Math.max(0, Number(cfg.get("copilotComposerInputGateEraseDelayMs", 120)) || 120),
            statusPattern: /ctrl\+s run command|ctrl\+q enqueue/i,
          },
          headerPattern: /github\s*copilot/i,
          modelPattern: /gpt-[0-9.]+|github\s*copilot/i,
          statusPattern: /loading environment|environment loaded|remaining reqs|ctrl\+s run command|ctrl\+q enqueue/i,
          promptPattern: /❯\s|type @ to mention files/i,
        },
        ux: {
          label: "Copilot PTY",
          sendTitle: "Send text to Copilot PTY",
          sendPrompt: "Text will be sent through the PTY-native Copilot session.",
          verifySuccess: (expected) => `Copilot PTY verify succeeded: '${expected}'.`,
          smokeSuccess: (iterations) =>
            `Copilot PTY smoke test passed ${iterations} iteration${iterations === 1 ? "" : "s"}.`,
          fallbackPrompt: (errorCode) => `Copilot PTY rebuild failed (${errorCode}). Enable fallback tool?`,
        },
      },
    },
  };
}

function getProfile(kind) {
  return getConfig().profiles[normalizeBackendKind(kind)];
}

function refreshSessionLimits(session) {
  session.maxRetryCount = getConfig().maxRetryCount;
}

function clearLastError(session) {
  session.lastErrorCode = null;
  session.lastErrorSummary = null;
  session.lastFailedCommand = null;
}

function setLastError(session, code, summary, command) {
  session.lastErrorCode = code;
  session.lastErrorSummary = summary;
  session.lastFailedCommand = command || null;
}

function setRecoveryState(session, nextState, reason, extra = {}) {
  if (session.recoveryState === nextState) return;
  const previousState = session.recoveryState;
  session.recoveryState = nextState;
  emitEvent("pty.state.changed", {
    kind: session.kind,
    sessionId: session.sessionId,
    from: previousState,
    to: nextState,
    reason,
    ...extra,
  });
}

function removeOutputWaiter(session, waiterId) {
  const waiter = session.outputWaiters.get(waiterId);
  if (!waiter) return;
  session.outputWaiters.delete(waiterId);
  if (waiter.timer) clearTimeout(waiter.timer);
}

function rejectAllOutputWaiters(session, error) {
  const waiters = Array.from(session.outputWaiters.values());
  session.outputWaiters.clear();
  for (const waiter of waiters) {
    if (waiter.timer) clearTimeout(waiter.timer);
    waiter.reject(error);
  }
}

function resolveOutputWaiters(session, text) {
  const normalizedChunk = normalizeOutputText(text);
  if (!normalizedChunk) return;

  for (const waiter of session.outputWaiters.values()) {
    waiter.buffer = `${waiter.buffer}${normalizedChunk}`.slice(-20000);
    if (hasMeaningfulProgressOutput(normalizedChunk)) {
      waiter.lastProgressAt = Date.now();
    }
    if (waiter.buffer.includes(waiter.expected)) {
      removeOutputWaiter(session, waiter.id);
      waiter.resolve({ ok: true, expected: waiter.expectedRaw, sessionId: session.sessionId });
    }
  }
}

function waitForOutputMatch(kind, options) {
  const session = getSession(kind);
  const expectedRaw = String(options.expected || "");
  const expected = normalizeOutputText(expectedRaw).trim();
  const timeoutMs = Math.max(1000, Number(options.timeoutMs) || getConfig().verifyTimeoutMs);
  const maxTimeoutMs = Math.max(timeoutMs, Number(options.maxTimeoutMs) || getConfig().verifyMaxTimeoutMs);
  const waiterId = `${session.kind}-waiter-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
  const startedAt = Date.now();

  return new Promise((resolve, reject) => {
    const waiter = {
      id: waiterId,
      expected,
      expectedRaw,
      buffer: normalizeOutputText(session.recentOutput),
      lastProgressAt: startedAt,
      resolve,
      reject,
      timer: null,
    };

    const tick = () => {
      if (!session.outputWaiters.has(waiterId)) return;
      const now = Date.now();
      if (waiter.buffer.includes(expected)) {
        removeOutputWaiter(session, waiterId);
        resolve({ ok: true, expected: expectedRaw, sessionId: session.sessionId });
        return;
      }
      if (now - startedAt >= maxTimeoutMs) {
        removeOutputWaiter(session, waiterId);
        reject(makeError(ERROR_CODES.PTY_VERIFY_TIMEOUT, `${options.label || "wait"} exceeded max timeout.`));
        return;
      }
      if (now - waiter.lastProgressAt >= timeoutMs) {
        removeOutputWaiter(session, waiterId);
        reject(makeError(ERROR_CODES.PTY_VERIFY_TIMEOUT, `${options.label || "wait"} timed out.`));
        return;
      }
      waiter.timer = setTimeout(tick, 100);
    };

    session.outputWaiters.set(waiterId, waiter);
    tick();
  });
}

function resetSessionHandles(session) {
  session.proc = null;
  session.bridgeControl = null;
  session.writeInput = null;
  session.csiUKeyboardProtocolEnabled = false;
  session.startupReady = false;
  session.startupReadyDeadlineAt = 0;
  session.startupSignals = {
    headerSeen: false,
    modelResolvedSeen: false,
    statusSeen: false,
    promptSeen: false,
  };
  session.recentOutput = "";
  session.lastOutputAt = 0;
}

function resetRuntimeStore() {
  runtimeStore = createInitialRuntimeStore();
}

function updateKeyboardProtocolState(session, text) {
  if (!text) return;
  const stateTransitions = Array.from(text.matchAll(/\x1b\[(?:>(\d+)u|(<u))/g));
  if (!stateTransitions.length) return;

  const lastTransition = stateTransitions[stateTransitions.length - 1];
  const enabled = Boolean(lastTransition[1] && Number(lastTransition[1]) > 0);
  if (session.csiUKeyboardProtocolEnabled === enabled) return;

  session.csiUKeyboardProtocolEnabled = enabled;
  emitEvent("pty.keyboard_protocol.changed", {
    kind: session.kind,
    sessionId: session.sessionId,
    protocol: "csi-u",
    enabled,
    modeValue: enabled ? Number(lastTransition[1]) : 0,
  });
}

function shouldWaitForProgrammaticSubmitSettle(profile, options) {
  if (profile.submitPolicy.settleDelayMs <= 0) return false;
  const settleTextModes = Array.isArray(profile.submitPolicy.settleTextModes)
    ? profile.submitPolicy.settleTextModes
    : ["csi-u-text"];
  if (!settleTextModes.includes(options.textMode)) return false;
  const textLength = Array.from(String(options.text || "")).length;
  if (textLength < profile.submitPolicy.settleMinTextLength) return false;
  return true;
}

function countProgrammaticSubmitTextLength(options) {
  return Array.from(String(options.text || "")).length;
}

function hasSemanticStartupReadySignal(session, profile) {
  if (session.startupSignals.promptSeen) return true;
  if (session.startupSignals.headerSeen && session.startupSignals.statusSeen) return true;
  if (session.startupSignals.headerSeen && session.startupSignals.modelResolvedSeen) return true;
  return session.startupSignals.modelResolvedSeen && session.startupSignals.statusSeen;
}

function maybeMarkStartupReady(session, profile) {
  if (session.startupReady) return;
  if (!hasSemanticStartupReadySignal(session, profile)) return;
  if (profile.startup.requireCsiU && !session.csiUKeyboardProtocolEnabled) return;
  const now = Date.now();
  if (!session.startupReadyDeadlineAt) {
    session.startupReadyDeadlineAt = now + getConfig().startupReadyDebounceMs;
    emitEvent("pty.startup.semantic_ready", {
      kind: session.kind,
      sessionId: session.sessionId,
      debounceMs: getConfig().startupReadyDebounceMs,
    });
    return;
  }
  if (now >= session.startupReadyDeadlineAt) {
    session.startupReady = true;
    emitEvent("pty.startup.ready", {
      kind: session.kind,
      sessionId: session.sessionId,
      startupSignals: session.startupSignals,
    });
  }
}

function updateStartupSignalState(session, profile, text) {
  const rawBuffer = `${session.recentOutput}\n${String(text || "")}`;
  const buffer = stripAnsi(rawBuffer).replace(/\r/g, "\n").slice(-24000);
  const semanticBuffer = toSemanticText(rawBuffer).slice(-12000);
  const previousSignals = JSON.stringify(session.startupSignals);

  session.recentOutput = buffer;

  if (profile.startup.headerPattern.test(buffer) || profile.startup.headerPattern.test(semanticBuffer)) {
    session.startupSignals.headerSeen = true;
  }
  if (
    (profile.startup.modelPattern.test(buffer) || profile.startup.modelPattern.test(semanticBuffer)) &&
    !/model:\s*loading/i.test(buffer) &&
    !/model:\s*loading/i.test(semanticBuffer)
  ) {
    session.startupSignals.modelResolvedSeen = true;
  }
  if (profile.startup.statusPattern.test(buffer) || profile.startup.statusPattern.test(semanticBuffer)) {
    session.startupSignals.statusSeen = true;
  }
  if (
    profile.startup.promptPattern.test(buffer) ||
    profile.startup.promptPattern.test(semanticBuffer) ||
    /[›>]\s*(run\s*\/|implement|explain|ask|what)/i.test(semanticBuffer)
  ) {
    session.startupSignals.promptSeen = true;
  }
  if (JSON.stringify(session.startupSignals) !== previousSignals) {
    emitEvent("pty.startup.signals", {
      kind: session.kind,
      sessionId: session.sessionId,
      startupSignals: session.startupSignals,
    });
  }
  maybeMarkStartupReady(session, profile);
}

async function waitForSessionReady(kind) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  const timeoutMs = getConfig().startupTimeoutMs;
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    if (!session.terminal) {
      throw makeError(ERROR_CODES.PTY_TERMINAL_DISPOSED, `${getProfile(kind).ux.label} terminal is not available.`);
    }
    maybeMarkStartupReady(session, profile);
    if (session.startupReady && typeof session.writeInput === "function") {
      return true;
    }
    await delay(100);
  }

  throw makeError(ERROR_CODES.PTY_VERIFY_TIMEOUT, `${getProfile(kind).ux.label} did not become ready in time.`);
}

async function waitForProgrammaticSubmitSettle(kind, options) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  if (!shouldWaitForProgrammaticSubmitSettle(profile, options)) return false;
  const textLength = countProgrammaticSubmitTextLength(options);
  emitEvent("pty.submit.settle_wait", {
    kind: session.kind,
    sessionId: session.sessionId,
    label: options.label,
    delayMs: profile.submitPolicy.settleDelayMs,
    reason: profile.submitPolicy.settleReason,
    textLength,
  });
  await delay(profile.submitPolicy.settleDelayMs);
  return true;
}

async function waitForFreshPromptStability(kind) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  const timeoutMs = Math.max(0, Number(profile.startup?.freshPromptStableTimeoutMs) || 0);
  const quietMs = Math.max(0, Number(profile.startup?.freshPromptQuietMs) || 0);
  const requiredPattern = profile.startup?.freshPromptRequiredPattern;

  if (timeoutMs <= 0 && quietMs <= 0 && !requiredPattern) return false;

  const startedAt = Date.now();
  while (Date.now() - startedAt < Math.max(timeoutMs, quietMs, 1000)) {
    if (!session.terminal) {
      throw makeError(ERROR_CODES.PTY_TERMINAL_DISPOSED, `${getProfile(kind).ux.label} terminal is not available.`);
    }

    const recentOutput = String(session.recentOutput || "");
    const patternReady = requiredPattern ? requiredPattern.test(recentOutput) : true;
    const quietReady = quietMs <= 0 || (session.lastOutputAt > 0 && Date.now() - session.lastOutputAt >= quietMs);

    if (patternReady && quietReady) {
      emitEvent("pty.startup.fresh_prompt_stable", {
        kind,
        sessionId: session.sessionId,
        quietMs,
        patternMatched: patternReady,
      });
      return true;
    }

    await delay(100);
  }

  throw makeError(ERROR_CODES.PTY_VERIFY_TIMEOUT, `${getProfile(kind).ux.label} fresh prompt did not stabilize in time.`);
}

async function waitForCopilotComposerInputReady(kind) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  const gate = profile.startup?.composerInputGate;

  if (kind !== BACKEND_KINDS.COPILOT || !gate?.enabled) return false;

  const attempts = Math.max(1, Number(gate.attempts) || 1);
  const timeoutMs = Math.max(250, Number(gate.timeoutMs) || 250);
  const retryDelayMs = Math.max(0, Number(gate.retryDelayMs) || 0);
  const eraseDelayMs = Math.max(0, Number(gate.eraseDelayMs) || 0);

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    if (!session.terminal) {
      throw makeError(ERROR_CODES.PTY_TERMINAL_DISPOSED, `${getProfile(kind).ux.label} terminal is not available.`);
    }

    try {
      session.terminal.show(false);
    } catch {
      // ignore focus failures; probe will still determine readiness.
    }

    await delay(100);

    const probeText = `ivy${Date.now().toString(36).slice(-4)}${attempt}`;
    const baselineRaw = String(session.recentOutput || "");
    const baselineNormalized = normalizeOutputText(baselineRaw);
    const probeNormalized = normalizeOutputText(probeText).trim();
    const probeOk = session.writeInput(probeText);
    if (!probeOk) {
      throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} composer probe text.`);
    }

    emitEvent("pty.startup.composer_input_probe.started", {
      kind,
      sessionId: session.sessionId,
      attempt,
      attempts,
      probeText,
      timeoutMs,
    });

    let matched = false;
    let matchReason = null;
    const startedAt = Date.now();
    while (Date.now() - startedAt < timeoutMs) {
      if (!session.terminal) {
        throw makeError(ERROR_CODES.PTY_TERMINAL_DISPOSED, `${getProfile(kind).ux.label} terminal is not available.`);
      }

      const recentRaw = String(session.recentOutput || "");
      const recentNormalized = normalizeOutputText(recentRaw);
      const echoedProbe = recentNormalized !== baselineNormalized && recentNormalized.includes(probeNormalized);

      if (echoedProbe) {
        matched = true;
        matchReason = "probe_echo";
        break;
      }

      await delay(50);
    }

    session.writeInput("\x7f".repeat(probeText.length));
    if (eraseDelayMs > 0) {
      await delay(eraseDelayMs);
    }

    if (matched) {
      emitEvent("pty.startup.composer_input_probe.succeeded", {
        kind,
        sessionId: session.sessionId,
        attempt,
        attempts,
        matchReason,
      });
      return true;
    }

    emitEvent("pty.startup.composer_input_probe.failed", {
      kind,
      sessionId: session.sessionId,
      attempt,
      attempts,
      timeoutMs,
    });

    if (retryDelayMs > 0 && attempt < attempts) {
      await delay(retryDelayMs);
    }
  }

  throw makeError(ERROR_CODES.PTY_VERIFY_TIMEOUT, `${getProfile(kind).ux.label} composer input did not become visible in time.`);
}

async function sendSubmitToPty(kind) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  if (typeof session.writeInput !== "function") {
    throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `${getProfile(kind).ux.label} session is not ready for submit.`);
  }

  if (profile.inputPolicy?.submitMode === "ctrl-s") {
    const ctrlSOk = session.writeInput(CTRL_S);
    if (!ctrlSOk) {
      throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} Ctrl+S submit.`);
    }
    return { ok: true, mode: "ctrl-s" };
  }

  if (profile.inputPolicy?.submitMode === "csi-u-enter") {
    const pressOk = session.writeInput(CSI_U_ENTER_PRESS);
    await delay(10);
    const releaseOk = session.writeInput(CSI_U_ENTER_RELEASE);
    if (!pressOk || !releaseOk) {
      throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} CSI u submit.`);
    }
    return { ok: true, mode: "csi-u-enter", pressOk, releaseOk };
  }

  if (profile.inputPolicy?.submitMode === "carriage-return") {
    const carriageReturnOk = session.writeInput("\r");
    if (!carriageReturnOk) {
      throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} carriage return.`);
    }
    return { ok: true, mode: "carriage-return" };
  }

  if (session.csiUKeyboardProtocolEnabled) {
    const pressOk = session.writeInput(CSI_U_ENTER_PRESS);
    await delay(10);
    const releaseOk = session.writeInput(CSI_U_ENTER_RELEASE);
    if (!pressOk || !releaseOk) {
      throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} CSI u submit.`);
    }
    return { ok: true, mode: "csi-u-enter", pressOk, releaseOk };
  }

  const carriageReturnOk = session.writeInput("\r");
  if (!carriageReturnOk) {
    throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} carriage return.`);
  }
  return { ok: true, mode: "carriage-return" };
}

async function sendTextToPty(kind, text) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  if (typeof session.writeInput !== "function") {
    throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `${getProfile(kind).ux.label} session is not ready for text input.`);
  }

  const normalizedText = String(text || "");
  if (profile.inputPolicy?.textMode === "direct-text") {
    const ok = session.writeInput(normalizedText);
    if (!ok) throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} text.`);
    return { ok: true, mode: "direct-text" };
  }

  if (!session.csiUKeyboardProtocolEnabled) {
    const ok = session.writeInput(normalizedText);
    if (!ok) throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} text.`);
    return { ok: true, mode: "direct-text" };
  }

  let wroteAny = false;
  for (const char of normalizedText) {
    const codePoint = char.codePointAt(0);
    const isPrintable = typeof codePoint === "number" && codePoint >= 0x20 && codePoint !== 0x7f;
    if (!isPrintable) {
      const fallbackOk = session.writeInput(normalizedText);
      if (!fallbackOk) {
        throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} fallback text.`);
      }
      return { ok: true, mode: "direct-text-fallback" };
    }
    const pressOk = session.writeInput(encodeCsiUKeyPress(codePoint));
    const releaseOk = session.writeInput(encodeCsiUKeyRelease(codePoint));
    if (!pressOk || !releaseOk) {
      throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `Failed to write ${getProfile(kind).ux.label} CSI u text input.`);
    }
    wroteAny = true;
  }

  if (!wroteAny && normalizedText) {
    throw makeError(ERROR_CODES.PTY_WRITE_FAILED, `No ${getProfile(kind).ux.label} text input was written.`);
  }

  return { ok: true, mode: "csi-u-text" };
}

function disposeCurrentTerminal(kind) {
  const session = getSession(kind);
  const terminal = session.terminal;
  if (!terminal) return false;
  try {
    terminal.dispose();
    return true;
  } catch {
    return false;
  }
}

async function promptForText(kind) {
  const profile = getProfile(kind);
  const text = await vscode.window.showInputBox({
    title: profile.ux.sendTitle,
    prompt: profile.ux.sendPrompt,
    placeHolder: "e.g. ping",
  });
  if (typeof text !== "string" || !text.trim()) return null;
  return text;
}

function createPtyTerminal(context, kind) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  resetSessionHandles(session);
  const writeEmitter = new vscode.EventEmitter();
  const closeEmitter = new vscode.EventEmitter();
  const workspaceRoot = getWorkspaceRootFsPath();
  const pythonExec = resolvePythonExecutable();
  const sessionId = `${kind}-pty-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;

  let bridgeProc;
  let bridgeControl;
  let closed = false;
  let sessionClosed = false;
  let closeKillTimer = null;
  let closeExpectation = null;
  let resolveSessionClosed;
  const sessionClosedPromise = new Promise((resolve) => {
    resolveSessionClosed = resolve;
  });

  const markExpectedClose = (reason) => {
    if (!closeExpectation) closeExpectation = { reason };
    const barrier = session.sessionCloseBarrier;
    if (barrier?.sessionId === sessionId) {
      barrier.closeRequested = true;
      barrier.closeReason = barrier.closeReason || reason;
    }
  };

  const getExpectedCloseReason = () => {
    if (closeExpectation?.reason) return closeExpectation.reason;
    const barrier = session.sessionCloseBarrier;
    if (barrier?.sessionId === sessionId && barrier.closeRequested) {
      return barrier.closeReason || "expected_close";
    }
    return null;
  };

  const finalizeSessionClose = (reason) => {
    if (sessionClosed) return;
    sessionClosed = true;
    if (closeKillTimer) {
      clearTimeout(closeKillTimer);
      closeKillTimer = null;
    }
    if (session.sessionCloseBarrier?.sessionId === sessionId) {
      session.sessionCloseBarrier = null;
    }
    emitEvent("pty.session.closed", { kind, sessionId, reason });
    resolveSessionClosed({ sessionId, reason });
  };

  const closeWithCode = (code = 0) => {
    if (closed) return;
    closed = true;
    emitEvent("pty.close.emitted", { kind, sessionId, code });
    closeEmitter.fire(code);
  };

  const pty = {
    onDidWrite: writeEmitter.event,
    onDidClose: closeEmitter.event,
    open: (initialDimensions) => {
      refreshSessionLimits(session);
      const dims = normalizeTerminalDimensions(initialDimensions);
      appendDebugEvent(kind, {
        type: "pty_open",
        sessionId,
        workspaceRoot,
        command: profile.command,
        pythonExec,
        initialDimensions: dims,
      });
      const launchText =
        `Launching ${profile.command} inside a Python PTY bridge...\r\n` +
        `cwd: ${workspaceRoot}\r\n` +
        `python: ${pythonExec}\r\n` +
        `size: ${dims.columns}x${dims.rows}\r\n\r\n`;
      writeEmitter.fire(launchText);
      appendLiveLog(kind, launchText.replace(/\r\n/g, "\n"));
      appendOutputLine(`[start:${kind}] ${profile.command} session=${sessionId}`);

      try {
        bridgeProc = childProcess.spawn(
          pythonExec,
          [
            BRIDGE_SCRIPT,
            "--cwd",
            workspaceRoot,
            "--cols",
            String(dims.columns),
            "--rows",
            String(dims.rows),
            "--",
            profile.command,
          ],
          {
            cwd: workspaceRoot,
            env: {
              ...process.env,
              TERM: process.env.TERM || "xterm-256color",
              COLORTERM: process.env.COLORTERM || "truecolor",
            },
            stdio: ["pipe", "pipe", "pipe", "pipe"],
          },
        );
      } catch (error) {
        const message = `Failed to start PTY session: ${String(error || "")}\r\n`;
        writeEmitter.fire(message);
        appendLiveLog(kind, message.replace(/\r\n/g, "\n"));
        appendDebugEvent(kind, { type: "spawn_failure", sessionId, error: String(error || "") });
        finalizeSessionClose("spawn_failure");
        closeWithCode(1);
        return;
      }

      session.proc = bridgeProc;
      session.bridgeControl = bridgeProc.stdio?.[3];
      session.sessionId = sessionId;
      session.writeInput = (text) => {
        const activeSession = isActiveSession(session, sessionId);
        const writable = activeSession && Boolean(bridgeProc?.stdin?.writable);
        appendDebugEvent(kind, {
          type: "write_input",
          sessionId,
          pid: bridgeProc?.pid,
          activeSession,
          writable,
          textPreview: toDebugPreview(text),
          textLength: String(text || "").length,
        });
        if (!writable) return false;
        bridgeProc.stdin.write(text);
        return true;
      };
      session.sessionCloseBarrier = {
        sessionId,
        promise: sessionClosedPromise,
        closeRequested: false,
        closeReason: null,
      };

      bridgeProc.stdout.on("data", (chunk) => {
        const text = Buffer.from(chunk).toString("utf8");
        const activeSession = isActiveSession(session, sessionId);
        if (activeSession) {
          session.lastOutputAt = Date.now();
          updateKeyboardProtocolState(session, text);
          updateStartupSignalState(session, profile, text);
        }
        appendDebugEvent(kind, {
          type: "stdout_data",
          sessionId,
          pid: bridgeProc.pid,
          activeSession,
          bytes: Buffer.byteLength(text, "utf8"),
          textPreview: toDebugPreview(text),
        });
        writeEmitter.fire(text);
        appendLiveLog(kind, text);
        if (activeSession) {
          resolveOutputWaiters(session, text);
        }
      });

      bridgeProc.stderr.on("data", (chunk) => {
        const text = Buffer.from(chunk).toString("utf8");
        const activeSession = isActiveSession(session, sessionId);
        if (activeSession) {
          session.lastOutputAt = Date.now();
        }
        appendDebugEvent(kind, {
          type: "stderr_data",
          sessionId,
          pid: bridgeProc.pid,
          activeSession,
          bytes: Buffer.byteLength(text, "utf8"),
          textPreview: toDebugPreview(text),
        });
        writeEmitter.fire(text);
        appendLiveLog(kind, text);
      });

      bridgeProc.on("error", (error) => {
        const activeSession = isActiveSession(session, sessionId);
        if (activeSession) {
          rejectAllOutputWaiters(
            session,
            makeError(ERROR_CODES.PTY_PIPE_BROKEN, `PTY process error: ${String(error || "")}`),
          );
        }
        appendDebugEvent(kind, {
          type: "process_error",
          sessionId,
          pid: bridgeProc.pid,
          activeSession,
          error: String(error || ""),
        });
        if (activeSession) {
          setLastError(
            session,
            ERROR_CODES.PTY_PIPE_BROKEN,
            `PTY process error: ${String(error || "")}`,
            session.lastFailedCommand,
          );
          setRecoveryState(session, RECOVERY_STATES.REBUILDABLE, "pty process error", {
            kind,
            sessionId,
            errorCode: ERROR_CODES.PTY_PIPE_BROKEN,
          });
        }
        finalizeSessionClose("process_error");
        closeWithCode(1);
      });

      bridgeProc.on("exit", (code, signal) => {
        const activeSession = isActiveSession(session, sessionId);
        const exitCode = typeof code === "number" ? code : 0;
        const commandSettingKey = getCommandSettingKey(kind);
        const summary =
          exitCode === 127
            ? `PTY launch failed: command '${profile.command}' is not available on PATH. Install the CLI or update ivyhouseTerminalPty.${commandSettingKey}.`
            : `PTY process exited code=${exitCode}${signal ? ` signal=${signal}` : ""}`;
        const expectedCloseReason = getExpectedCloseReason();
        const expectedClose = Boolean(expectedCloseReason);
        const exitText = `\r\n[pty:${kind}] ${summary}\r\n`;
        writeEmitter.fire(exitText);
        appendLiveLog(kind, `\n[pty:${kind}] ${summary}\n`);
        appendDebugEvent(kind, {
          type: "process_exit",
          sessionId,
          pid: bridgeProc.pid,
          code: exitCode,
          signal: signal || null,
          activeSession,
          expectedClose,
          expectedCloseReason,
        });
        if (activeSession) {
          rejectAllOutputWaiters(session, makeError(ERROR_CODES.PTY_CHILD_EXITED, summary));
          if (!expectedClose) {
            setLastError(session, ERROR_CODES.PTY_CHILD_EXITED, summary, session.lastFailedCommand);
            setRecoveryState(session, RECOVERY_STATES.REBUILDABLE, "pty process exited", {
              kind,
              sessionId,
              errorCode: ERROR_CODES.PTY_CHILD_EXITED,
            });
          } else {
            emitEvent("pty.process_exit.expected", {
              kind,
              sessionId,
              code: exitCode,
              signal: signal || null,
              reason: expectedCloseReason,
            });
          }
          resetSessionHandles(session);
          if (session.sessionId === sessionId) {
            session.sessionId = null;
          }
        }
        finalizeSessionClose(expectedCloseReason || "process_exit");
        closeWithCode(exitCode);
      });
    },
    close: () => {
      markExpectedClose("terminal_close_requested");
      appendDebugEvent(kind, {
        type: "pty_close_requested",
        sessionId,
        pid: bridgeProc?.pid,
        hasProc: Boolean(bridgeProc),
        reason: getExpectedCloseReason(),
      });
      if (!bridgeProc) {
        rejectAllOutputWaiters(
          session,
          makeError(ERROR_CODES.PTY_TERMINAL_DISPOSED, "PTY terminal was closed before output waiters completed."),
        );
        resetSessionHandles(session);
        finalizeSessionClose("close_without_process");
        closeWithCode(0);
        return;
      }

      try {
        bridgeProc.kill("SIGTERM");
      } catch {
        // ignore
      }

      const forceKillDelayMs = Math.max(0, Number(profile.closePolicy?.forceKillDelayMs) || 0);
      if (forceKillDelayMs > 0) {
        closeKillTimer = setTimeout(() => {
          if (sessionClosed) return;
          if (bridgeProc && bridgeProc.exitCode === null && bridgeProc.signalCode === null) {
            appendDebugEvent(kind, {
              type: "pty_close_force_kill",
              sessionId,
              pid: bridgeProc.pid,
              reason: getExpectedCloseReason(),
              delayMs: forceKillDelayMs,
            });
            try {
              bridgeProc.kill("SIGKILL");
            } catch {
              // ignore
            }
          }
          closeKillTimer = null;
        }, forceKillDelayMs);
      }

      rejectAllOutputWaiters(
        session,
        makeError(ERROR_CODES.PTY_TERMINAL_DISPOSED, "PTY terminal was closed before output waiters completed."),
      );
      closeWithCode(0);
    },
    handleInput: (data) => {
      appendDebugEvent(kind, {
        type: "handle_input",
        sessionId,
        pid: bridgeProc?.pid,
        writable: Boolean(bridgeProc?.stdin?.writable),
        textPreview: toDebugPreview(data),
      });
      if (!bridgeProc?.stdin?.writable) return;
      try {
        bridgeProc.stdin.write(data);
      } catch {
        // ignore
      }
    },
    setDimensions: (dimensions) => {
      const normalized = normalizeTerminalDimensions(dimensions);
      appendDebugEvent(kind, { type: "set_dimensions", sessionId, dimensions: normalized });
      if (!session.bridgeControl?.writable) return;
      try {
        session.bridgeControl.write(
          encodePtyControlMessage({
            type: "resize",
            cols: normalized.columns,
            rows: normalized.rows,
          }),
        );
      } catch (error) {
        appendDebugEvent(kind, {
          type: "set_dimensions_forward_error",
          sessionId,
          error: String(error || ""),
          dimensions: normalized,
        });
      }
    },
  };

  const terminal = vscode.window.createTerminal({ name: profile.terminalName, pty });
  session.sessionId = sessionId;
  session.terminal = terminal;
  context.subscriptions.push(writeEmitter, closeEmitter, terminal);
  emitEvent("terminal_created", { kind, sessionId, terminalName: profile.terminalName });
  return terminal;
}

function ensureStarted(context, kind) {
  const session = getSession(kind);
  if (session.terminal) {
    try {
      session.terminal.show(true);
    } catch {
      // ignore
    }
    return session.terminal;
  }
  const terminal = createPtyTerminal(context, kind);
  terminal.show(true);
  return terminal;
}

async function closeActiveSessionAndWait(kind) {
  const session = getSession(kind);
  const barrier = session.sessionCloseBarrier;
  if (!session.terminal) return false;

  emitEvent("pty.close.wait.started", { kind, sessionId: session.sessionId });
  disposeCurrentTerminal(kind);

  if (!barrier?.promise) {
    emitEvent("pty.close.wait.succeeded", { kind, sessionId: session.sessionId, immediate: true });
    session.terminal = null;
    return true;
  }

  const result = await Promise.race([
    barrier.promise,
    delay(5000).then(() => ({ timeout: true })),
  ]);

  if (result?.timeout) {
    emitEvent("pty.close.wait.failed", { kind, sessionId: session.sessionId, reason: "timeout" });
    throw makeError(ERROR_CODES.PTY_TERMINAL_DISPOSED, `${getProfile(kind).ux.label} close wait timed out.`);
  }

  session.terminal = null;
  emitEvent("pty.close.wait.succeeded", { kind, sessionId: result?.sessionId || null, reason: result?.reason || null });
  return true;
}

function handleManagedFailure(session, command, error, requestId) {
  const code = error?.code || ERROR_CODES.PTY_WRITE_FAILED;
  const summary = error?.message || String(error || "Unknown PTY error.");
  setLastError(session, code, summary, command);

  emitEvent("pty.command.failed", {
    kind: session.kind,
    command,
    requestId,
    sessionId: session.sessionId,
    errorCode: code,
    summary,
  });

  if (SESSION_LEVEL_ERRORS.has(code)) {
    setRecoveryState(session, RECOVERY_STATES.REBUILDABLE, `session-level failure during ${command}`, {
      kind: session.kind,
      sessionId: session.sessionId,
      errorCode: code,
    });
    return;
  }

  if (session.retryCount < session.maxRetryCount) {
    setRecoveryState(session, RECOVERY_STATES.RETRYABLE, `retryable failure during ${command}`, {
      kind: session.kind,
      sessionId: session.sessionId,
      errorCode: code,
    });
    return;
  }

  setLastError(
    session,
    ERROR_CODES.PTY_RETRY_EXHAUSTED,
    `Retry budget exhausted after ${command} failure: ${summary}`,
    command,
  );
  emitEvent("pty.retry.exhausted", {
    kind: session.kind,
    requestId,
    sessionId: session.sessionId,
    attempt: session.retryCount,
    maxAttempts: session.maxRetryCount,
    errorCode: ERROR_CODES.PTY_RETRY_EXHAUSTED,
  });
  setRecoveryState(session, RECOVERY_STATES.REBUILDABLE, `retry exhausted during ${command}`, {
    kind: session.kind,
    sessionId: session.sessionId,
    errorCode: ERROR_CODES.PTY_RETRY_EXHAUSTED,
  });
}

async function runManagedCommand(kind, command, fn) {
  const session = getSession(kind);
  const requestId = makeRequestId();
  emitEvent("pty.command.started", { kind, command, requestId, sessionId: session.sessionId });
  try {
    const result = await fn(requestId);
    clearLastError(session);
    session.retryCount = 0;
    if (session.recoveryState !== RECOVERY_STATES.NORMAL) {
      setRecoveryState(session, RECOVERY_STATES.NORMAL, `${command} succeeded`, {
        kind: session.kind,
        sessionId: session.sessionId,
        requestId,
      });
    }
    emitEvent("pty.command.succeeded", { kind, command, requestId, sessionId: session.sessionId });
    return result;
  } catch (error) {
    handleManagedFailure(session, command, error, requestId);
    throw error;
  }
}

async function startCommand(context, kind) {
  return runManagedCommand(kind, "start", async () => {
    rotateCurrentArtifacts(kind, "start");
    ensureStarted(context, kind);
    await waitForSessionReady(kind);
  });
}

async function restartCommand(context, kind) {
  return runManagedCommand(kind, "restart", async () => {
    await closeActiveSessionAndWait(kind);
    rotateCurrentArtifacts(kind, "restart");
    ensureStarted(context, kind);
    await waitForSessionReady(kind);
  });
}

async function rotateArtifactsCommand(args) {
  const reason = typeof args?.reason === "string" && args.reason.trim() ? args.reason.trim() : "new-workflow";
  const requestedKind = args?.kind;
  const kinds = requestedKind ? [normalizeBackendKind(requestedKind)] : Object.values(BACKEND_KINDS);
  const payload = kinds.map((kind) => ({ kind, ...rotateCurrentArtifacts(kind, reason) }));
  appendOutputLine(JSON.stringify(payload, null, 2));
  outputChannel.show(true);
  vscode.window.showInformationMessage(`PTY artifacts rotated for ${kinds.join(", ")}.`);
}

async function sendCommand(context, kind, args) {
  const session = getSession(kind);
  const payload = parseSendArgs(args, false);
  const text = payload.text || (await promptForText(kind));
  if (!text) return;

  session.lastAction = { type: "send", args: { text, submit: payload.submit } };
  await runManagedCommand(kind, "send", async () => {
    ensureStarted(context, kind);
    await waitForSessionReady(kind);
    const result = await sendTextToPty(kind, text);
    emitEvent("send_text_result", {
      kind,
      sessionId: session.sessionId,
      ok: result.ok,
      mode: result.mode,
      textPreview: toDebugPreview(text),
    });

    if (payload.submit) {
      await waitForProgrammaticSubmitSettle(kind, { label: `${kind}-send`, text, textMode: result.mode });
      const submitResult = await sendSubmitToPty(kind);
      emitEvent("send_submit_result", {
        kind,
        sessionId: session.sessionId,
        ok: submitResult.ok,
        mode: submitResult.mode,
        pressOk: submitResult.pressOk,
        releaseOk: submitResult.releaseOk,
      });
    }
  });
}

async function submitCommand(context, kind) {
  const session = getSession(kind);
  session.lastAction = { type: "submit", args: {} };
  await runManagedCommand(kind, "submit", async () => {
    ensureStarted(context, kind);
    await waitForSessionReady(kind);
    const result = await sendSubmitToPty(kind);
    emitEvent("send_submit_result", {
      kind,
      sessionId: session.sessionId,
      ok: result.ok,
      mode: result.mode,
      pressOk: result.pressOk,
      releaseOk: result.releaseOk,
    });
  });
}

async function startFreshSession(context, kind) {
  const profile = getProfile(kind);
  await closeActiveSessionAndWait(kind).catch(() => false);
  ensureStarted(context, kind);
  await waitForSessionReady(kind);
  const freshPromptDelayMs = Math.max(0, Number(profile.startup?.freshPromptDelayMs) || 0);
  if (freshPromptDelayMs > 0) {
    emitEvent("pty.startup.fresh_prompt_delay", {
      kind,
      sessionId: getSession(kind).sessionId,
      delayMs: freshPromptDelayMs,
    });
    await delay(freshPromptDelayMs);
  }
  await waitForFreshPromptStability(kind);
  await waitForCopilotComposerInputReady(kind);
}

function formatSmokeStepLabel(label, iteration, iterations) {
  if (iterations <= 1) return label;
  return `${label}#${iteration}/${iterations}`;
}

async function runPromptStep(kind, options) {
  const session = getSession(kind);
  emitEvent(options.startedEventType, {
    kind,
    requestId: options.requestId,
    sessionId: session.sessionId,
    label: options.label,
    prompt: options.prompt,
    expected: options.expected,
  });

  try {
    const textResult = await sendTextToPty(kind, options.prompt);
    emitEvent("send_text_result", {
      kind,
      sessionId: session.sessionId,
      ok: textResult.ok,
      mode: textResult.mode,
      textPreview: toDebugPreview(options.prompt),
    });
    await waitForProgrammaticSubmitSettle(kind, {
      label: options.label,
      text: options.prompt,
      textMode: textResult.mode,
    });
    const submitResult = await sendSubmitToPty(kind);
    emitEvent("send_submit_result", {
      kind,
      sessionId: session.sessionId,
      ok: submitResult.ok,
      mode: submitResult.mode,
      pressOk: submitResult.pressOk,
      releaseOk: submitResult.releaseOk,
    });
    const waitResult = await waitForOutputMatch(kind, {
      expected: options.expected,
      label: options.label,
      timeoutMs: options.timeoutMs,
      maxTimeoutMs: options.maxTimeoutMs,
    });
    emitEvent(options.succeededEventType, {
      kind,
      requestId: options.requestId,
      sessionId: session.sessionId,
      label: options.label,
      expected: options.expected,
      waitResult,
    });
    return waitResult;
  } catch (error) {
    emitEvent(options.failedEventType, {
      kind,
      requestId: options.requestId,
      sessionId: session.sessionId,
      label: options.label,
      errorCode: error?.code || ERROR_CODES.PTY_VERIFY_TIMEOUT,
      summary: error?.message || String(error || "Unknown PTY verify failure."),
    });
    throw error;
  }
}

async function runSmokeIteration(context, kind, requestId, iteration, iterations, timeoutMs) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  emitEvent("pty.smoke.iteration.started", { kind, requestId, sessionId: session.sessionId, iteration, iterations });

  try {
    await startFreshSession(context, kind);
    for (const step of profile.smokeSpec) {
      await runPromptStep(kind, {
        requestId,
        label: formatSmokeStepLabel(step.label, iteration, iterations),
        prompt: step.prompt,
        expected: step.expected,
        timeoutMs,
        maxTimeoutMs: getConfig().verifyMaxTimeoutMs,
        startedEventType: "pty.smoke.step.started",
        succeededEventType: "pty.smoke.step.succeeded",
        failedEventType: "pty.smoke.step.failed",
      });
    }
    emitEvent("pty.smoke.iteration.succeeded", { kind, requestId, sessionId: session.sessionId, iteration, iterations });
  } catch (error) {
    emitEvent("pty.smoke.iteration.failed", {
      kind,
      requestId,
      sessionId: session.sessionId,
      iteration,
      iterations,
      errorCode: error?.code || ERROR_CODES.PTY_VERIFY_TIMEOUT,
      summary: error?.message || String(error || "Unknown PTY smoke failure."),
    });
    throw error;
  }
}

async function verifyCommand(context, kind, args) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  const prompt = typeof args?.prompt === "string" && args.prompt.trim() ? args.prompt : profile.verifySpec.prompt;
  const expected = typeof args?.expected === "string" && args.expected.trim() ? args.expected : profile.verifySpec.expected;
  const timeoutMs = Math.max(1000, Number(args?.timeoutMs) || getConfig().verifyTimeoutMs);
  const maxTimeoutMs = Math.max(timeoutMs, Number(args?.maxTimeoutMs) || getConfig().verifyMaxTimeoutMs);

  session.lastAction = { type: "verify", args: { prompt, expected, timeoutMs, maxTimeoutMs } };
  await runManagedCommand(kind, "verify", async (requestId) => {
    ensureStarted(context, kind);
    await waitForSessionReady(kind);
    await runPromptStep(kind, {
      requestId,
      label: "verify",
      prompt,
      expected,
      timeoutMs,
      maxTimeoutMs,
      startedEventType: "pty.verify.started",
      succeededEventType: "pty.verify.succeeded",
      failedEventType: "pty.verify.failed",
    });
    session.lastVerify = { ok: true, expected, at: new Date().toISOString() };
    vscode.window.showInformationMessage(profile.ux.verifySuccess(expected));
  });
}

async function smokeTestCommand(context, kind, args) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  const defaultIterations = kind === BACKEND_KINDS.COPILOT ? 1 : getConfig().smokeIterationCount;
  const iterations = Math.max(1, Number(args?.iterations) || defaultIterations);

  session.lastAction = { type: "smokeTest", args: { iterations } };
  await runManagedCommand(kind, "smokeTest", async (requestId) => {
    for (let iteration = 1; iteration <= iterations; iteration += 1) {
      await runSmokeIteration(context, kind, requestId, iteration, iterations, getConfig().verifyTimeoutMs);
    }

    session.lastSmokeTest = {
      ok: true,
      at: new Date().toISOString(),
      iterations,
      steps: profile.smokeSpec.map((step) => `${step.prompt}->${step.expected}`),
    };
    vscode.window.showInformationMessage(profile.ux.smokeSuccess(iterations));
  });
}

async function showRecoveryStatusCommand(args) {
  const requestedKind = args?.kind;
  const kinds = requestedKind ? [normalizeBackendKind(requestedKind)] : Object.values(BACKEND_KINDS);
  const payload = kinds.map((kind) => {
    const session = getSession(kind);
    const artifacts = resolveArtifactNames(kind);
    return {
      kind,
      recoveryState: session.recoveryState,
      sessionId: session.sessionId,
      terminalName: getProfile(kind).terminalName,
      lastErrorCode: session.lastErrorCode,
      lastErrorSummary: session.lastErrorSummary,
      lastFailedCommand: session.lastFailedCommand,
      retryCount: session.retryCount,
      maxRetryCount: session.maxRetryCount,
      fallbackDecision: session.fallbackDecision,
      lastFallbackHandoff: session.lastFallbackHandoff,
      lastVerify: session.lastVerify,
      lastSmokeTest: session.lastSmokeTest,
      liveLogPath: resolveCapturePath(artifacts.live),
      debugLogPath: resolveCapturePath(artifacts.debug),
    };
  });
  appendOutputLine(JSON.stringify(payload, null, 2));
  outputChannel.show(true);
  vscode.window.showInformationMessage(`PTY status inspected for ${kinds.join(", ")}.`);
}

async function retryLastActionCommand(context, kind) {
  const session = getSession(kind);
  if (!session.lastAction) {
    vscode.window.showWarningMessage(`No ${getProfile(kind).ux.label} action is available to retry.`);
    return;
  }

  if (session.retryCount >= session.maxRetryCount) {
    setLastError(session, ERROR_CODES.PTY_RETRY_EXHAUSTED, "Retry budget exhausted; rebuild the session instead.", session.lastAction.type);
    setRecoveryState(session, RECOVERY_STATES.REBUILDABLE, "retry budget exhausted", {
      kind,
      sessionId: session.sessionId,
      errorCode: ERROR_CODES.PTY_RETRY_EXHAUSTED,
    });
    vscode.window.showWarningMessage(`Retry budget exhausted for ${getProfile(kind).ux.label}. Use Rebuild PTY Session.`);
    return;
  }

  session.retryCount += 1;
  emitEvent("pty.retry.scheduled", {
    kind,
    sessionId: session.sessionId,
    attempt: session.retryCount,
    maxAttempts: session.maxRetryCount,
    errorCode: session.lastErrorCode,
  });
  setRecoveryState(session, RECOVERY_STATES.RETRYABLE, "manual retry requested", {
    kind,
    sessionId: session.sessionId,
    errorCode: session.lastErrorCode,
  });

  if (session.lastAction.type === "send") {
    await sendCommand(context, kind, session.lastAction.args);
    return;
  }
  if (session.lastAction.type === "submit") {
    await submitCommand(context, kind);
    return;
  }
  if (session.lastAction.type === "verify") {
    await verifyCommand(context, kind, session.lastAction.args);
    return;
  }
  if (session.lastAction.type === "smokeTest") {
    await smokeTestCommand(context, kind, session.lastAction.args);
    return;
  }

  vscode.window.showWarningMessage(`Retry for action '${session.lastAction.type}' is not implemented.`);
}

function getFallbackCommandIds(kind) {
  if (kind === BACKEND_KINDS.CODEX) {
    return {
      start: "ivyhouseTerminalFallback.startCodex",
      sendInteractive: "ivyhouseTerminalFallback.sendToCodex",
      capture: "ivyhouseTerminalFallback.captureCodexOutput",
    };
  }

  return {
    start: "ivyhouseTerminalFallback.startCopilot",
    sendInteractive: "ivyhouseTerminalFallback.sendToCopilot",
    capture: null,
  };
}

async function handoffToFallbackRuntime(context, kind, trigger) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  const commandIds = getFallbackCommandIds(kind);
  const lastAction = session.lastAction
    ? {
        type: session.lastAction.type,
        args: session.lastAction.args || {},
      }
    : null;

  emitEvent("pty.fallback.handoff.started", {
    kind,
    sessionId: session.sessionId,
    trigger,
    lastActionType: lastAction?.type || null,
  });

  try {
    const bridgeResult = await vscode.commands.executeCommand("ivyhouseTerminalFallback.startBridge");
    const terminalResult = await vscode.commands.executeCommand(commandIds.start);

    let replay = {
      attempted: false,
      status: "not_attempted",
      reason: lastAction ? "unsupported_action" : "no_last_action",
      actionType: lastAction?.type || null,
    };

    if (lastAction?.type === "send") {
      replay = {
        attempted: true,
        status: "replayed-send",
        reason: null,
        actionType: lastAction.type,
        result: await vscode.commands.executeCommand("ivyhouseTerminalFallback.sendLiteral", {
          terminalKind: kind,
          text: String(lastAction.args?.text || ""),
          submit: Boolean(lastAction.args?.submit),
        }),
      };
    } else if (lastAction?.type === "submit") {
      replay = {
        attempted: true,
        status: "replayed-submit",
        reason: null,
        actionType: lastAction.type,
        result: await vscode.commands.executeCommand("ivyhouseTerminalFallback.sendLiteral", {
          terminalKind: kind,
          text: "",
          submit: true,
        }),
      };
    }

    const manualContinuationRequired = replay.status === "not_attempted";
    const handoff = {
      at: new Date().toISOString(),
      trigger,
      terminalName: terminalResult?.terminalName || null,
      bridgeRunning: Boolean(bridgeResult?.running),
      lastActionType: lastAction?.type || null,
      replay,
      manualContinuationRequired,
    };

    session.lastFallbackHandoff = handoff;
    setRecoveryState(session, RECOVERY_STATES.FALLBACK_ACTIVE, "fallback handoff completed", {
      kind,
      sessionId: session.sessionId,
      trigger,
      replayStatus: replay.status,
    });

    emitEvent("pty.fallback.handoff.succeeded", {
      kind,
      sessionId: session.sessionId,
      trigger,
      terminalName: handoff.terminalName,
      bridgeRunning: handoff.bridgeRunning,
      replayStatus: replay.status,
      manualContinuationRequired,
    });

    if (manualContinuationRequired) {
      emitEvent("pty.manualActionRequired", {
        kind,
        sessionId: session.sessionId,
        reason: "fallback handoff ready; continue in fallback runtime",
        errorCode: ERROR_CODES.PTY_FALLBACK_REQUIRED,
        suggestedActions: [commandIds.sendInteractive, commandIds.capture].filter(Boolean),
      });
      vscode.window.showWarningMessage(
        `${profile.ux.label} 已切到 fallback runtime。bridge 與 terminal 已就位，但最後一步 '${lastAction?.type || "none"}' 需要在 fallback session 繼續。`,
      );
    } else {
      vscode.window.showWarningMessage(
        `${profile.ux.label} 已切到 fallback runtime，並已自動接手最後一步 ${replay.status}。`,
      );
    }

    return handoff;
  } catch (error) {
    const summary = `Fallback handoff failed: ${String(error?.message || error || "unknown_error")}`;
    session.lastFallbackHandoff = {
      at: new Date().toISOString(),
      trigger,
      failed: true,
      summary,
      lastActionType: lastAction?.type || null,
    };
    setLastError(session, ERROR_CODES.PTY_FALLBACK_HANDOFF_FAILED, summary, session.lastFailedCommand);
    setRecoveryState(session, RECOVERY_STATES.REBUILDABLE, "fallback handoff failed", {
      kind,
      sessionId: session.sessionId,
      errorCode: ERROR_CODES.PTY_FALLBACK_HANDOFF_FAILED,
    });
    emitEvent("pty.fallback.handoff.failed", {
      kind,
      sessionId: session.sessionId,
      trigger,
      errorCode: ERROR_CODES.PTY_FALLBACK_HANDOFF_FAILED,
      summary,
    });
    emitEvent("pty.manualActionRequired", {
      kind,
      sessionId: session.sessionId,
      reason: "fallback accepted but handoff failed",
      errorCode: ERROR_CODES.PTY_FALLBACK_HANDOFF_FAILED,
      suggestedActions: ["ivyhouseTerminalPty.showRecoveryStatus", commandIds.start].filter(Boolean),
    });
    vscode.window.showErrorMessage(summary);
    throw makeError(ERROR_CODES.PTY_FALLBACK_HANDOFF_FAILED, summary);
  }
}

async function enableFallbackCommand(context, kind, trigger = "manual") {
  const session = getSession(kind);
  session.fallbackDecision = FALLBACK_DECISIONS.ACCEPTED;
  emitEvent("pty.fallback.accepted", {
    kind,
    sessionId: session.sessionId,
    reason: session.lastErrorSummary || `${trigger} acceptance`,
    trigger,
  });
  return handoffToFallbackRuntime(context, kind, trigger);
}

async function declineFallbackCommand(kind) {
  const session = getSession(kind);
  session.fallbackDecision = FALLBACK_DECISIONS.DECLINED;
  setLastError(session, ERROR_CODES.PTY_FALLBACK_DECLINED, "User declined fallback after PTY failure.", session.lastFailedCommand);
  setRecoveryState(session, RECOVERY_STATES.FALLBACK_DECLINED, "user declined fallback", {
    kind,
    sessionId: session.sessionId,
    errorCode: ERROR_CODES.PTY_FALLBACK_DECLINED,
  });
  emitEvent("pty.fallback.declined", { kind, sessionId: session.sessionId, reason: "user declined fallback" });
  emitEvent("pty.manualActionRequired", {
    kind,
    sessionId: session.sessionId,
    reason: "fallback declined",
    errorCode: ERROR_CODES.PTY_MANUAL_INTERVENTION_REQUIRED,
    suggestedActions: ["retryLastAction", "rebuildSession", "enableFallback"],
  });
  vscode.window.showWarningMessage(
    `${getProfile(kind).ux.label} fallback declined. PTY is now in manual recovery mode; use Retry, Rebuild, or Enable Fallback later.`,
  );
}

async function promptForFallback(context, kind, errorCode, reason) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  session.fallbackDecision = FALLBACK_DECISIONS.PENDING;
  session.fallbackOfferedAt = new Date().toISOString();
  setRecoveryState(session, RECOVERY_STATES.PROMPTING_FALLBACK, reason, {
    kind,
    sessionId: session.sessionId,
    errorCode,
  });
  emitEvent("pty.fallback.prompted", { kind, sessionId: session.sessionId, reason, errorCode });

  const choice = await vscode.window.showWarningMessage(profile.ux.fallbackPrompt(errorCode), "Enable Fallback", "Not Now");
  if (choice === "Enable Fallback") {
    await enableFallbackCommand(context, kind, "consented-handoff");
    return;
  }
  await declineFallbackCommand(kind);
}

async function rebuildSessionCommand(context, kind) {
  const session = getSession(kind);
  const profile = getProfile(kind);
  await runManagedCommand(kind, "rebuildSession", async () => {
    emitEvent("pty.rebuild.started", { kind, oldSessionId: session.sessionId || null });
    await closeActiveSessionAndWait(kind).catch(() => false);
    ensureStarted(context, kind);
    try {
      await waitForSessionReady(kind);
      await runPromptStep(kind, {
        requestId: makeRequestId(),
        label: "verify-after-rebuild",
        prompt: profile.verifySpec.prompt,
        expected: profile.verifySpec.expected,
        timeoutMs: getConfig().verifyTimeoutMs,
        maxTimeoutMs: getConfig().verifyMaxTimeoutMs,
        startedEventType: "pty.verify.started",
        succeededEventType: "pty.verify.succeeded",
        failedEventType: "pty.verify.failed",
      });
      emitEvent("pty.rebuild.succeeded", { kind, oldSessionId: null, newSessionId: session.sessionId || null });
    } catch (error) {
      const errorCode = error?.code || ERROR_CODES.PTY_REBUILD_FAILED;
      emitEvent("pty.rebuild.failed", { kind, oldSessionId: null, errorCode });
      setLastError(
        session,
        ERROR_CODES.PTY_VERIFY_AFTER_REBUILD_FAILED,
        error?.message || "Verify failed after rebuild.",
        "rebuildSession",
      );
      await promptForFallback(context, kind, ERROR_CODES.PTY_VERIFY_AFTER_REBUILD_FAILED, "verify failed after rebuild");
      throw makeError(ERROR_CODES.PTY_VERIFY_AFTER_REBUILD_FAILED, error?.message || "Verify failed after rebuild.");
    }
  });
}

async function resetSessionStateCommand(args) {
  const requestedKind = args?.kind;
  const kinds = requestedKind ? [normalizeBackendKind(requestedKind)] : Object.values(BACKEND_KINDS);
  for (const kind of kinds) {
    try {
      await closeActiveSessionAndWait(kind);
    } catch {
      // ignore
    }
  }
  resetRuntimeStore();
  appendOutputLine(`[reset] PTY runtime state reset for ${kinds.join(", ")}.`);
  vscode.window.showInformationMessage(`IvyHouse Terminal PTY session state reset for ${kinds.join(", ")}.`);
}

function registerKindedCommand(context, commandId, handler) {
  context.subscriptions.push(vscode.commands.registerCommand(commandId, handler));
}

function activate(context) {
  outputChannel = vscode.window.createOutputChannel("IvyHouse Terminal PTY");
  resetRuntimeStore();

  context.subscriptions.push(outputChannel);
  context.subscriptions.push(
    vscode.window.onDidCloseTerminal((terminal) => {
      for (const kind of Object.values(BACKEND_KINDS)) {
        const session = getSession(kind);
        if (!session.terminal) continue;
        if (terminal !== session.terminal) continue;
        appendDebugEvent(kind, {
          type: "terminal_closed_by_vscode",
          sessionId: session.sessionId || null,
          terminalName: terminal.name,
          exitCode: terminal.exitStatus?.code,
          exitReason: terminal.exitStatus?.reason,
        });
        session.terminal = null;
      }
    }),
  );

  registerKindedCommand(context, "ivyhouseTerminalPty.start", async () => startCommand(context, BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.restart", async () => restartCommand(context, BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.send", async (args) => sendCommand(context, BACKEND_KINDS.CODEX, args));
  registerKindedCommand(context, "ivyhouseTerminalPty.submit", async () => submitCommand(context, BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.verify", async (args) => verifyCommand(context, BACKEND_KINDS.CODEX, args));
  registerKindedCommand(context, "ivyhouseTerminalPty.smokeTest", async (args) => smokeTestCommand(context, BACKEND_KINDS.CODEX, args));
  registerKindedCommand(context, "ivyhouseTerminalPty.retryLastAction", async (args) => retryLastActionCommand(context, args?.kind || BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.rebuildSession", async (args) => rebuildSessionCommand(context, args?.kind || BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.enableFallback", async (args) => enableFallbackCommand(context, args?.kind || BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.declineFallback", async (args) => declineFallbackCommand(args?.kind || BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.showRecoveryStatus", async (args) => showRecoveryStatusCommand(args));
  registerKindedCommand(context, "ivyhouseTerminalPty.rotateArtifacts", async (args) => rotateArtifactsCommand(args));
  registerKindedCommand(context, "ivyhouseTerminalPty.resetSessionState", async (args) => resetSessionStateCommand(args));

  registerKindedCommand(context, "ivyhouseTerminalPty.startCodex", async () => startCommand(context, BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.startCopilot", async () => startCommand(context, BACKEND_KINDS.COPILOT));
  registerKindedCommand(context, "ivyhouseTerminalPty.restartCodex", async () => restartCommand(context, BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.restartCopilot", async () => restartCommand(context, BACKEND_KINDS.COPILOT));
  registerKindedCommand(context, "ivyhouseTerminalPty.sendToCodex", async (args) => sendCommand(context, BACKEND_KINDS.CODEX, args));
  registerKindedCommand(context, "ivyhouseTerminalPty.sendToCopilot", async (args) => sendCommand(context, BACKEND_KINDS.COPILOT, args));
  registerKindedCommand(context, "ivyhouseTerminalPty.submitCodex", async () => submitCommand(context, BACKEND_KINDS.CODEX));
  registerKindedCommand(context, "ivyhouseTerminalPty.submitCopilot", async () => submitCommand(context, BACKEND_KINDS.COPILOT));
  registerKindedCommand(context, "ivyhouseTerminalPty.verifyCodex", async (args) => verifyCommand(context, BACKEND_KINDS.CODEX, args));
  registerKindedCommand(context, "ivyhouseTerminalPty.verifyCopilot", async (args) => verifyCommand(context, BACKEND_KINDS.COPILOT, args));
  registerKindedCommand(context, "ivyhouseTerminalPty.smokeTestCodex", async (args) => smokeTestCommand(context, BACKEND_KINDS.CODEX, args));
  registerKindedCommand(context, "ivyhouseTerminalPty.smokeTestCopilot", async (args) => smokeTestCommand(context, BACKEND_KINDS.COPILOT, args));

  const cfg = getConfig();
  for (const kind of Object.values(BACKEND_KINDS)) {
    if (!cfg.profiles[kind].autoStart) continue;
    startCommand(context, kind).catch((error) => {
      console.error(error);
      vscode.window.showErrorMessage(`${cfg.profiles[kind].ux.label} autoStart failed: ${String(error?.message || error)}`);
    });
  }
}

function deactivate() {
  for (const kind of Object.values(BACKEND_KINDS)) {
    disposeCurrentTerminal(kind);
  }
  if (outputChannel) {
    outputChannel.dispose();
  }
}

module.exports = {
  activate,
  deactivate,
};
