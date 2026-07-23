// PDF Generation Skill — HTML→PDF via weasyprint or headless Chrome
import { execSync } from "child_process";
import fs from "fs";
import path from "path";

export class PDFGenerationSkill {
  name = "pdf";
  description = "Generate PDFs from HTML content or URLs";

  tools() {
    return [
      {
        name: "from_html",
        description: "Generate a PDF from an HTML string",
        inputSchema: {
          type: "object",
          properties: {
            html: { type: "string", description: "HTML content to convert" },
            output: { type: "string", description: "Output file path" }
          },
          required: ["html", "output"]
        }
      },
      {
        name: "from_url",
        description: "Generate a PDF from a web page URL",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string", description: "URL to convert" },
            output: { type: "string", description: "Output file path" }
          },
          required: ["url", "output"]
        }
      }
    ];
  }

  async from_html(args) {
    const { html, output } = args;
    try {
      const tmpFile = `/tmp/zes-pdf-${Date.now()}.html`;
      fs.mkdirSync(path.dirname(output), { recursive: true });
      fs.writeFileSync(tmpFile, html, "utf-8");

      // Try weasyprint first, then headless chrome
      try {
        execSync(`weasyprint "${tmpFile}" "${output}"`, { timeout: 30000 });
        fs.unlinkSync(tmpFile);
        return { success: true, data: { path: output } };
      } catch {
        // Try headless Chrome
        try {
          execSync(`chromium --headless --disable-gpu --print-to-pdf="${output}" "file://${tmpFile}"`, { timeout: 30000 });
          fs.unlinkSync(tmpFile);
          return { success: true, data: { path: output } };
        } catch {
          fs.unlinkSync(tmpFile);
          return { success: false, error: "PDF generation requires weasyprint or headless chromium" };
        }
      }
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async from_url(args) {
    const { url, output } = args;
    try {
      fs.mkdirSync(path.dirname(output), { recursive: true });
      try {
        execSync(`weasyprint "${url}" "${output}"`, { timeout: 30000 });
        return { success: true, data: { path: output } };
      } catch {
        execSync(`chromium --headless --disable-gpu --print-to-pdf="${output}" "${url}"`, { timeout: 30000 });
        return { success: true, data: { path: output } };
      }
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}
