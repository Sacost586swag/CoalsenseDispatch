export class AppError extends Error {
  code: string;
  message_es: string;
  recoverable: boolean;
  next_actions: string[];

  constructor(code: string, message_es: string, recoverable: boolean, next_actions: string[]) {
    super(message_es);
    this.name = "AppError";
    this.code = code;
    this.message_es = message_es;
    this.recoverable = recoverable;
    this.next_actions = [...next_actions];
  }

  toJSON(): { code: string; message_es: string; recoverable: boolean; next_actions: string[] } {
    return {
      code: this.code,
      message_es: this.message_es,
      recoverable: this.recoverable,
      next_actions: [...this.next_actions],
    };
  }
}
