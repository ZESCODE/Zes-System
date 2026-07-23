// Spreadsheet Skill — Read/write CSV and Excel files
import fs from "fs";
import path from "path";
import { execSync } from "child_process";

export class SpreadsheetSkill {
  name = "spreadsheet";
  description = "Read and write CSV and Excel spreadsheet files";

  tools() {
    return [
      {
        name: "read_csv",
        description: "Read a CSV file and return rows as arrays",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Absolute path to CSV file" },
            delimiter: { type: "string", description: "Delimiter character", default: "," }
          },
          required: ["path"]
        }
      },
      {
        name: "write_csv",
        description: "Write rows of data to a CSV file",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Output file path" },
            rows: { type: "array", items: { type: "array", items: { type: "string" } }, description: "Array of rows, each row is an array of strings" }
          },
          required: ["path", "rows"]
        }
      },
      {
        name: "read_excel",
        description: "Read an Excel (.xlsx) file and return sheet data",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Absolute path to .xlsx file" }
          },
          required: ["path"]
        }
      },
      {
        name: "write_excel",
        description: "Write data to an Excel (.xlsx) file",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Output file path" },
            data: { type: "array", items: { type: "array" }, description: "Array of rows" },
            sheetName: { type: "string", description: "Sheet name", default: "Sheet1" }
          },
          required: ["path", "data"]
        }
      }
    ];
  }

  async read_csv(args) {
    try {
      const content = fs.readFileSync(args.path, "utf-8");
      const delim = args.delimiter || ",";
      const rows = content.split("\n")
        .filter(line => line.trim())
        .map(line => line.split(delim).map(cell => cell.trim().replace(/^"|"$/g, "")));
      return { success: true, data: { rows } };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async write_csv(args) {
    try {
      fs.mkdirSync(path.dirname(args.path), { recursive: true });
      const lines = args.rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","));
      fs.writeFileSync(args.path, lines.join("\n"), "utf-8");
      return { success: true, data: { path: args.path, rows: args.rows.length } };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async read_excel(args) {
    try {
      const cmd = `python3 -c "
import json, sys
try:
    import openpyxl
    wb = openpyxl.load_workbook('${args.path.replace(/'/g, "'\\''")}', data_only=True)
    data = {s: [[c for c in row] for row in ws.iter_rows(values_only=True)] for s, ws in [(ws.title, ws) for ws in wb.worksheets]}
    print(json.dumps(data))
except Exception as e:
    print(json.dumps({'error': str(e)}))
"`;
      const output = execSync(cmd, { timeout: 15000, encoding: "utf-8" });
      const result = JSON.parse(output);
      if (result.error) return { success: false, error: result.error };
      return { success: true, data: result };
    } catch (e) {
      return { success: false, error: e.message + " — Install openpyxl: pip install openpyxl" };
    }
  }

  async write_excel(args) {
    try {
      const jsonData = JSON.stringify(args.data);
      const sheetName = args.sheetName || "Sheet1";
      const cmd = `python3 -c "
import json, sys
try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '${sheetName.replace(/'/g, "'\\''")}'
    for row in json.loads('''${jsonData.replace(/'/g, "'\\''")}'''):
        ws.append(row)
    wb.save('${args.path.replace(/'/g, "'\\''")}')
    print(json.dumps({'success': True}))
except Exception as e:
    print(json.dumps({'error': str(e)}))
"`;
      fs.mkdirSync(path.dirname(args.path), { recursive: true });
      const output = execSync(cmd, { timeout: 15000, encoding: "utf-8" });
      return JSON.parse(output);
    } catch (e) {
      return { success: false, error: e.message + " — Install openpyxl: pip install openpyxl" };
    }
  }
}
