// Schema Validation — ported from OpenClaw's llm-core validation.ts
// JSON Schema compatible tool argument validation

export class SchemaValidator {
  constructor() {
    this._validators = new Map();
  }

  register(name, schema) {
    this._validators.set(name, schema);
    return this;
  }

  validate(name, args) {
    const schema = this._validators.get(name);
    if (!schema) return { valid: true, errors: [] };
    return this._validateValue(args, schema, `tool.${name}`);
  }

  _validateValue(value, schema, path) {
    let errors = [];

    // Type check
    if (schema.type === 'object' && (typeof value !== 'object' || value === null || Array.isArray(value))) {
      errors.push(`${path}: expected object, got ${typeof value}`);
      return { valid: false, errors };
    }
    if (schema.type === 'string' && typeof value !== 'string') {
      errors.push(`${path}: expected string, got ${typeof value}`);
    }
    if (schema.type === 'number' && typeof value !== 'number') {
      errors.push(`${path}: expected number, got ${typeof value}`);
    }
    if (schema.type === 'integer' && (!Number.isInteger(value))) {
      errors.push(`${path}: expected integer, got ${typeof value}`);
    }
    if (schema.type === 'boolean' && typeof value !== 'boolean') {
      errors.push(`${path}: expected boolean, got ${typeof value}`);
    }
    if (schema.type === 'array') {
      if (!Array.isArray(value)) {
        errors.push(`${path}: expected array, got ${typeof value}`);
      } else if (schema.items) {
        for (let i = 0; i < value.length; i++) {
          errors.push(...this._validateValue(value[i], schema.items, `${path}[${i}]`).errors);
        }
      }
    }

    // Object properties check
    if (schema.type === 'object' && schema.properties && typeof value === 'object' && value !== null) {
      // Check required properties
      if (Array.isArray(schema.required)) {
        for (const key of schema.required) {
          if (!(key in value)) {
            errors.push(`${path}.${key}: required field missing`);
          }
        }
      }
      // Check property types
      for (const [key, propSchema] of Object.entries(schema.properties)) {
        if (key in value && value[key] !== undefined) {
          errors.push(...this._validateValue(value[key], propSchema, `${path}.${key}`).errors);
        }
      }
      // Warn about unexpected properties (but don't fail)
    }

    return { valid: errors.length === 0, errors };
  }
}
