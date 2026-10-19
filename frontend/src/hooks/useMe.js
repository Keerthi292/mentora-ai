import { useEffect, useState } from "react";

import { api } from "../services/api";

// One request shared by every component that uses the user (greetings, theme)
let mePromise = null;
const listeners = new Set();

function loadMe() {
  mePromise ??= api.get("/api/me").catch((err) => {
    mePromise = null; // try again next time
    throw err;
  });
  return mePromise;
}

/** First name to greet the user with, or "" if unknown / still the placeholder. */
function firstName(me) {
  const name = me?.full_name?.trim() || "";
  if (!name || name === "Demo User") return "";
  return name.split(/\s+/)[0];
}

/**
 * The current user ({ id, full_name, email, theme }), or null while loading or
 * if the backend can't be reached. `update({ full_name?, theme? })` saves the
 * changes and updates every component that uses this hook.
 */
function useMe() {
  const [me, setMe] = useState(null);

  useEffect(() => {
    let active = true;
    loadMe()
      .then((data) => active && setMe(data))
      .catch(() => {}); // greetings just leave the name out
    listeners.add(setMe);
    return () => {
      active = false;
      listeners.delete(setMe);
    };
  }, []);

  const update = async (changes) => {
    const updated = await api.patch("/api/me", changes);
    mePromise = Promise.resolve(updated);
    listeners.forEach((set) => set(updated));
  };

  return { me, name: firstName(me), update };
}

export default useMe;
