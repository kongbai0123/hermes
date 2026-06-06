import { nanoid } from "nanoid";
import { Attachment } from "@/types/chat";

export type DataUrlReader = (file: File) => Promise<string>;

export const readFileAsDataUrl: DataUrlReader = (file: File) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("Unable to read image attachment."));
    reader.readAsDataURL(file);
  });

export async function imageFileToAttachment(
  file: File,
  readAsDataUrl: DataUrlReader = readFileAsDataUrl,
): Promise<Attachment> {
  return {
    id: nanoid(),
    name: file.name || `pasted-image-${Date.now()}.png`,
    size: file.size,
    type: file.type || "image/png",
    dataUrl: await readAsDataUrl(file),
  };
}

export async function clipboardItemsToImageAttachments(
  items: DataTransferItemList | DataTransferItem[],
  readAsDataUrl: DataUrlReader = readFileAsDataUrl,
): Promise<Attachment[]> {
  const attachments: Attachment[] = [];

  for (const item of Array.from(items)) {
    if (item.kind !== "file" || !item.type.startsWith("image/")) continue;
    const file = item.getAsFile();
    if (!file) continue;
    attachments.push(await imageFileToAttachment(file, readAsDataUrl));
  }

  return attachments;
}

export function attachmentsToPromptNote(attachments: Attachment[]): string {
  const imageAttachments = attachments.filter((attachment) => attachment.type?.startsWith("image/"));
  if (!imageAttachments.length) return "";

  const lines = imageAttachments.map(
    (attachment, index) =>
      `${index + 1}. ${attachment.name} (${attachment.type || "image"}, ${attachment.size} bytes)`,
  );
  return `\n\n[使用者已貼上圖片附件]\n${lines.join("\n")}`;
}
