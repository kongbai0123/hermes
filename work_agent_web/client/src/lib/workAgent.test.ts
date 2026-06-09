import { describe, expect, it } from "vitest";
import { WORK_AGENT_MODELS } from "./workAgent";

describe("WORK_AGENT_MODELS", () => {
  it("contains installed and downloadable model entries for the model picker", () => {
    const installed = WORK_AGENT_MODELS.filter((model) => model.availability === "installed");
    const downloadable = WORK_AGENT_MODELS.filter((model) => model.availability === "downloadable");

    expect(installed.map((model) => model.id)).toContain("ollama-gemma4");
    expect(downloadable.length).toBeGreaterThanOrEqual(3);
    expect(downloadable[0]).toMatchObject({
      provider: "ollama",
      downloadName: expect.any(String),
      sizeGb: expect.any(Number),
      minRamGb: expect.any(Number),
    });
  });
});
