import { describe, expect, it } from "vitest";
import {
  attachmentsToPromptNote,
  clipboardItemsToImageAttachments,
  imageFileToAttachment,
} from "./attachments";

function makeClipboardItem(file: File, type = file.type): DataTransferItem {
  return {
    kind: "file",
    type,
    getAsFile: () => file,
    getAsString: () => undefined,
    webkitGetAsEntry: () => null,
  } as unknown as DataTransferItem;
}

describe("image attachments", () => {
  it("converts an image file into a previewable attachment", async () => {
    const file = new File(["png"], "capture.png", { type: "image/png" });

    const attachment = await imageFileToAttachment(file, async () => "data:image/png;base64,cG5n");

    expect(attachment.name).toBe("capture.png");
    expect(attachment.type).toBe("image/png");
    expect(attachment.dataUrl).toBe("data:image/png;base64,cG5n");
  });

  it("extracts only image files from clipboard items", async () => {
    const image = new File(["png"], "capture.png", { type: "image/png" });
    const text = new File(["txt"], "note.txt", { type: "text/plain" });

    const attachments = await clipboardItemsToImageAttachments(
      [makeClipboardItem(image), makeClipboardItem(text)],
      async (file) => `data:${file.type};base64,test`,
    );

    expect(attachments).toHaveLength(1);
    expect(attachments[0].name).toBe("capture.png");
    expect(attachments[0].dataUrl).toBe("data:image/png;base64,test");
  });

  it("adds a concise image note for the backend prompt", () => {
    const note = attachmentsToPromptNote([
      {
        id: "image-1",
        name: "capture.png",
        size: 128,
        type: "image/png",
        dataUrl: "data:image/png;base64,test",
      },
    ]);

    expect(note).toContain("使用者已貼上圖片附件");
    expect(note).toContain("capture.png");
  });
});
