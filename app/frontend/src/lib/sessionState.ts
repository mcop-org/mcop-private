import { useEffect, useState, type Dispatch, type SetStateAction } from "react";

function readSessionValue<T>(key: string, initialValue: T): T {
  if (typeof window === "undefined") {
    return initialValue;
  }
  try {
    const raw = window.sessionStorage.getItem(key);
    return raw === null ? initialValue : (JSON.parse(raw) as T);
  } catch {
    return initialValue;
  }
}

function writeSessionValue<T>(key: string, value: T) {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore storage failures and keep the page state functional.
  }
}

function clearSessionValue(key: string) {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.sessionStorage.removeItem(key);
  } catch {
    // Ignore storage failures and keep the page state functional.
  }
}

export function useSessionStorageState<T>(key: string, initialValue: T) {
  const [state, setState] = useState<T>(() => readSessionValue(key, initialValue));

  useEffect(() => {
    writeSessionValue(key, state);
  }, [key, state]);

  function resetState(nextValue: T) {
    clearSessionValue(key);
    setState(nextValue);
  }

  return { state, setState: setState as Dispatch<SetStateAction<T>>, resetState };
}
