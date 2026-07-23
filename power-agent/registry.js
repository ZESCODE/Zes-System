// Skill Registry — Unified interface for registering and dispatching skills
// Each skill implements: { name, description, tools(), execute(toolName, args) }

export class SkillRegistry {
  constructor() {
    this.skills = new Map();
  }

  register(name, skillInstance) {
    this.skills.set(name, skillInstance);
  }

  get(name) {
    return this.skills.get(name);
  }

  list() {
    return Array.from(this.skills.keys());
  }

  async execute(skillName, method, args = {}) {
    const skill = this.skills.get(skillName);
    if (!skill) {
      throw new Error('Skill "' + skillName + '" not found. Available: ' + this.list().join(", "));
    }
    const fn = skill[method];
    if (typeof fn !== "function") {
      throw new Error('Method "' + method + '" not found on skill "' + skillName + '"');
    }
    return fn.call(skill, args);
  }

  toolDefinitions() {
    const tools = [];
    for (const [name, skill] of this.skills) {
      if (typeof skill.tools === "function") {
        for (const tool of skill.tools()) {
          tools.push({
            name: name + "_" + tool.name,
            description: tool.description,
            inputSchema: tool.inputSchema
          });
        }
      }
    }
    return tools;
  }
}
