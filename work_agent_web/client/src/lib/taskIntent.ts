export type TaskCapability =
  | "web_research"
  | "workspace_read"
  | "code_edit"
  | "shell_command"
  | "gui_action"
  | "reasoning_only";

export type TaskIntentName =
  | "market_price_lookup"
  | "fresh_information_lookup"
  | "code_edit"
  | "workspace_analysis"
  | "gui_action"
  | "reasoning_only";

export interface TaskIntent {
  intent: TaskIntentName;
  requiredCapability: TaskCapability;
  disallowedCapabilities: TaskCapability[];
  needsFreshData: boolean;
  requiredEvidence: string[];
  rationale: string;
}

const FRESH_DATA_KEYWORDS = [
  "現在",
  "目前",
  "今天",
  "最新",
  "近期",
  "即時",
  "價格",
  "市價",
  "多少錢",
  "哪裡買",
  "新聞",
  "2026",
];

const PRICE_KEYWORDS = ["價格", "市價", "多少錢", "報價", "哪裡買", "購買"];
const CODE_KEYWORDS = ["實作", "修 bug", "修bug", "修改", "改版", "新增功能", "重構", "測試"];
const WORKSPACE_KEYWORDS = ["專案", "檔案", "程式碼", "repo", "repository", "資料夾"];
const GUI_KEYWORDS = ["點擊", "打開頁面", "輸入到", "按下", "瀏覽器操作", "畫面上"];

export function classifyTaskIntent(prompt: string): TaskIntent {
  const normalized = prompt.toLowerCase();
  const hasFreshData = includesAny(normalized, FRESH_DATA_KEYWORDS);
  const hasPrice = includesAny(normalized, PRICE_KEYWORDS);

  if (hasPrice || (hasFreshData && /ddr|ram|記憶體|商品|硬碟|顯卡|cpu/.test(normalized))) {
    return {
      intent: "market_price_lookup",
      requiredCapability: "web_research",
      disallowedCapabilities: ["gui_action"],
      needsFreshData: true,
      requiredEvidence: ["source_links", "price_range", "checked_date"],
      rationale: "User asks for current market price, so the answer needs fresh external sources.",
    };
  }

  if (hasFreshData) {
    return {
      intent: "fresh_information_lookup",
      requiredCapability: "web_research",
      disallowedCapabilities: ["gui_action"],
      needsFreshData: true,
      requiredEvidence: ["source_links", "checked_date"],
      rationale: "User asks for current or latest information.",
    };
  }

  if (includesAny(normalized, CODE_KEYWORDS)) {
    return {
      intent: "code_edit",
      requiredCapability: "code_edit",
      disallowedCapabilities: ["gui_action"],
      needsFreshData: false,
      requiredEvidence: ["changed_files", "verification"],
      rationale: "User asks for implementation or code changes.",
    };
  }

  if (includesAny(normalized, WORKSPACE_KEYWORDS)) {
    return {
      intent: "workspace_analysis",
      requiredCapability: "workspace_read",
      disallowedCapabilities: ["gui_action"],
      needsFreshData: false,
      requiredEvidence: ["file_references"],
      rationale: "User asks about local project or files.",
    };
  }

  if (includesAny(normalized, GUI_KEYWORDS)) {
    return {
      intent: "gui_action",
      requiredCapability: "gui_action",
      disallowedCapabilities: [],
      needsFreshData: false,
      requiredEvidence: ["explicit_user_approval"],
      rationale: "User explicitly asks for visible UI interaction.",
    };
  }

  return {
    intent: "reasoning_only",
    requiredCapability: "reasoning_only",
    disallowedCapabilities: ["gui_action"],
    needsFreshData: false,
    requiredEvidence: ["direct_answer"],
    rationale: "User asks a stable reasoning or explanation question.",
  };
}

export function renderTaskIntentForPrompt(intent: TaskIntent): string {
  return [
    "Context Router Decision:",
    `intent: ${intent.intent}`,
    `requiredCapability: ${intent.requiredCapability}`,
    `disallowedCapabilities: ${intent.disallowedCapabilities.join(", ") || "none"}`,
    `needsFreshData: ${intent.needsFreshData}`,
    `requiredEvidence: ${intent.requiredEvidence.join(", ")}`,
    `rationale: ${intent.rationale}`,
    "Available capabilities are web_research, workspace_read, code_edit, shell_command, gui_action_requires_approval, reasoning_only.",
    "Do not invent unavailable tools such as product_search or price_query unless they are explicitly listed as available.",
    "If required evidence cannot be produced, report the missing capability instead of pretending the task is complete.",
  ].join("\n");
}

function includesAny(value: string, keywords: string[]) {
  return keywords.some((keyword) => value.includes(keyword.toLowerCase()));
}
