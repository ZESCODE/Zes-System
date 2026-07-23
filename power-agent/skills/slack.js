// Slack Skill — Send messages via Slack API
export class SlackSkill {
  name = "slack";
  description = "Send messages to Slack channels";

  tools() {
    return [
      {
        name: "send_message",
        description: "Send a message to a Slack channel",
        inputSchema: {
          type: "object",
          properties: {
            channel: { type: "string", description: "Slack channel ID or name (e.g. C12345 or #general)" },
            text: { type: "string", description: "Message text to send" },
            token: { type: "string", description: "Slack Bot User OAuth Token (xoxb-...)" }
          },
          required: ["channel", "text", "token"]
        }
      }
    ];
  }

  async send_message(args) {
    try {
      const { channel, text, token } = args;
      const response = await fetch("https://slack.com/api/chat.postMessage", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ channel, text })
      });
      const result = await response.json();
      if (result.ok) {
        return { success: true, data: { ts: result.ts, channel: result.channel } };
      }
      return { success: false, error: result.error || "Unknown Slack API error" };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}
