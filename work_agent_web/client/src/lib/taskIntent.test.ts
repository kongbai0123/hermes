import { describe, expect, it } from "vitest";
import { classifyTaskIntent, renderTaskIntentForPrompt } from "./taskIntent";

describe("taskIntent", () => {
  it("routes current market price questions to web research and blocks GUI", () => {
    const intent = classifyTaskIntent("麻煩幫我了解現在一條DDR4 16G的價格要多少");

    expect(intent).toMatchObject({
      intent: "market_price_lookup",
      requiredCapability: "web_research",
      needsFreshData: true,
    });
    expect(intent.disallowedCapabilities).toContain("gui_action");
    expect(intent.requiredEvidence).toContain("source_links");
    expect(intent.requiredEvidence).toContain("price_range");
  });

  it("routes implementation requests to code editing", () => {
    const intent = classifyTaskIntent("幫我實作 Context Router 並修 bug");

    expect(intent).toMatchObject({
      intent: "code_edit",
      requiredCapability: "code_edit",
      needsFreshData: false,
    });
    expect(intent.disallowedCapabilities).not.toContain("workspace_read");
  });

  it("renders available capability boundaries for prompts", () => {
    const rendered = renderTaskIntentForPrompt(
      classifyTaskIntent("今天 DDR4 16GB 價格")
    );

    expect(rendered).toContain("requiredCapability: web_research");
    expect(rendered).toContain("disallowedCapabilities: gui_action");
    expect(rendered).toContain("Do not invent unavailable tools");
  });
});
