// REST API Skill — HTTP client for external APIs
// Supports GET, POST, PUT, PATCH, DELETE with JSON body

export class RESTAPISkill {
  name = "api";
  description = "Make HTTP requests to external APIs";

  tools() {
    return [
      {
        name: "get",
        description: "Perform an HTTP GET request",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string", description: "Full URL to send GET request to" },
            headers: { type: "object", description: "Optional HTTP headers as key-value pairs" }
          },
          required: ["url"]
        }
      },
      {
        name: "post",
        description: "Perform an HTTP POST request with JSON body",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string", description: "Full URL to send POST request to" },
            body: { type: "object", description: "JSON body to send" },
            headers: { type: "object", description: "Optional HTTP headers" }
          },
          required: ["url"]
        }
      },
      {
        name: "put",
        description: "Perform an HTTP PUT request with JSON body",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string" },
            body: { type: "object" },
            headers: { type: "object" }
          },
          required: ["url"]
        }
      },
      {
        name: "delete",
        description: "Perform an HTTP DELETE request",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string" },
            headers: { type: "object" }
          },
          required: ["url"]
        }
      }
    ];
  }

  async _fetch(method, args) {
    const options = {
      method,
      headers: { "Content-Type": "application/json", ...(args.headers || {}) }
    };
    if (args.body && method !== "GET" && method !== "DELETE") {
      options.body = JSON.stringify(args.body);
    }
    try {
      const response = await fetch(args.url, options);
      const contentType = response.headers.get("content-type") || "";
      let data;
      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        data = await response.text();
      }
      return {
        success: true,
        data: {
          status: response.status,
          statusText: response.statusText,
          body: data,
          headers: Object.fromEntries(response.headers.entries())
        }
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async get(args) { return this._fetch("GET", args); }
  async post(args) { return this._fetch("POST", args); }
  async put(args) { return this._fetch("PUT", args); }
  async delete(args) { return this._fetch("DELETE", args); }
}
