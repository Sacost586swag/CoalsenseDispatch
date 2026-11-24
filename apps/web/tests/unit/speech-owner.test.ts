import assert from "node:assert/strict";
import { test } from "node:test";
import { SpeechOwners } from "../../src/features/workspace/speech-owner.ts";

test("a new owner ends the old reading; old cleanup and late events cannot cancel the new notice", () => {
  const owners = new SpeechOwners();
  const reading = Symbol();
  const notice = Symbol();
  let oldEnd = () => {};
  let newEnd = () => {};
  let stopped = 0;
  let oldDone = 0;
  let newDone = 0;
  assert.equal(
    owners.start(
      reading,
      (end) => {
        oldEnd = end;
      },
      () => {
        stopped += 1;
      },
      () => {
        oldDone += 1;
      },
    ),
    true,
  );
  assert.equal(
    owners.start(
      notice,
      (end) => {
        newEnd = end;
      },
      () => {
        stopped += 1;
      },
      () => {
        newDone += 1;
      },
    ),
    true,
  );
  assert.equal(oldDone, 1);
  owners.cancel(reading);
  oldEnd();
  assert.equal(stopped, 1);
  assert.equal(newDone, 0);
  newEnd();
  newEnd();
  assert.equal(newDone, 1);
});

test("only the active owner can pause or resume; errors do not change ownership", () => {
  const owners = new SpeechOwners();
  const reading = Symbol();
  let calls = 0;
  owners.start(
    reading,
    () => {},
    () => {},
    () => {},
  );
  assert.equal(
    owners.control(Symbol(), () => {
      calls += 1;
    }),
    false,
  );
  assert.equal(
    owners.control(reading, () => {
      throw new Error("unavailable");
    }),
    false,
  );
  assert.equal(
    owners.control(reading, () => {
      calls += 1;
    }),
    true,
  );
  assert.equal(calls, 1);
});

test("failed cancellation blocks replacement until the engine can be stopped", () => {
  const owners = new SpeechOwners();
  const reading = Symbol();
  let blocked = true;
  let plays = 0;
  owners.start(
    reading,
    () => {},
    () => {
      if (blocked) throw new Error("unavailable");
    },
    () => {},
  );
  assert.equal(
    owners.start(
      Symbol(),
      () => {
        plays += 1;
      },
      () => {},
      () => {},
    ),
    false,
  );
  assert.equal(plays, 0);
  blocked = false;
  assert.equal(owners.cancel(reading), true);
  assert.equal(
    owners.start(
      Symbol(),
      () => {
        plays += 1;
      },
      () => {},
      () => {},
    ),
    true,
  );
  assert.equal(plays, 1);
});

test("synchronous completion and play failure cannot leave a phantom reading", () => {
  const owners = new SpeechOwners();
  let done = 0;
  assert.equal(
    owners.start(
      Symbol(),
      (end) => end(),
      () => {},
      () => {
        done += 1;
      },
    ),
    false,
  );
  assert.equal(
    owners.start(
      Symbol(),
      () => {
        throw new Error("unavailable");
      },
      () => {},
      () => {
        done += 1;
      },
    ),
    false,
  );
  assert.equal(done, 2);
});
