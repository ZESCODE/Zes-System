// OCR Skill — Extract text from images via Tesseract
import { execSync } from "child_process";

export class OCRSkill {
  name = "ocr";
  description = "Extract text from images using Tesseract OCR";

  tools() {
    return [
      {
        name: "extract",
        description: "Extract text from an image file",
        inputSchema: {
          type: "object",
          properties: {
            imagePath: { type: "string", description: "Absolute path to image file (PNG, JPG, etc.)" },
            language: { type: "string", description: "OCR language (e.g. eng, fra)", default: "eng" }
          },
          required: ["imagePath"]
        }
      },
      {
        name: "extract_from_screenshot",
        description: "Take a CDP screenshot and extract text from it",
        inputSchema: {
          type: "object",
          properties: {
            language: { type: "string", description: "OCR language", default: "eng" }
          }
        }
      }
    ];
  }

  async extract(args) {
    try {
      const { imagePath, language } = args;
      const cmd = `tesseract "${imagePath}" stdout -l ${language || "eng"} 2>/dev/null`;
      const text = execSync(cmd, { timeout: 30000, encoding: "utf-8" });
      return { success: true, data: { text: text.trim(), length: text.trim().length } };
    } catch (e) {
      return { success: false, error: e.message + " — Install tesseract: apt install tesseract" };
    }
  }

  async extract_from_screenshot(args) {
    try {
      // First take a screenshot using CDP, then OCR it
      const { CDPSkill } = await import("./cdp.js");
      const cdp = new CDPSkill();
      const ss = await cdp.screenshot({});
      if (!ss.success) return ss;
      const tmpPath = `/tmp/zes-ocr-${Date.now()}.png`;
      const base64 = ss.data.data;
      execSync(`echo "${base64}" | base64 -d > "${tmpPath}"`, { timeout: 10000 });
      const result = await this.extract({ imagePath: tmpPath, language: args.language || "eng" });
      execSync(`rm "${tmpPath}"`, { timeout: 5000 });
      return result;
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}
