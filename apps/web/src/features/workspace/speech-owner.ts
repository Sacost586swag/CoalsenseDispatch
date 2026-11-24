type SpeechRequest = { owner: symbol; stop: () => void; done: () => void };

/** One local engine, distinct owners. No utterance text is kept in this coordinator. */
export class SpeechOwners {
  private active: SpeechRequest | undefined;

  start(
    owner: symbol,
    play: (ended: () => void) => void,
    stop: () => void,
    done: () => void,
  ): boolean {
    if (this.active && !this.cancel(this.active.owner)) return false;
    const request = { owner, stop, done };
    this.active = request;
    const ended = () => {
      if (this.active !== request) return;
      this.active = undefined;
      request.done();
    };
    try {
      play(ended);
    } catch {
      this.cancel(owner);
      return false;
    }
    return this.active === request;
  }

  cancel(owner: symbol): boolean {
    const request = this.active;
    if (!request || request.owner !== owner) return true;
    try {
      request.stop();
    } catch {
      return false;
    }
    // A native end event may have completed the request during stop().
    if (this.active === request) {
      this.active = undefined;
      request.done();
    }
    return true;
  }

  control(owner: symbol, action: () => void): boolean {
    if (this.active?.owner !== owner) return false;
    try {
      action();
      return true;
    } catch {
      return false;
    }
  }
}
