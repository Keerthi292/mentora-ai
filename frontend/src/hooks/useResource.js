import { useCallback, useEffect, useState } from "react";

import { api } from "../services/api";

/**
 * Load a list from the backend and create / update / delete items in it.
 *
 * Example: const { items, loading, error, create, update, remove } = useResource("/api/skills");
 *
 * After every change the list is reloaded from the backend, so the page always
 * shows exactly what is saved (including the backend's sort order).
 */
function useResource(basePath) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await api.get(basePath));
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [basePath]);

  useEffect(() => {
    reload();
  }, [reload]);

  // These throw on failure, so the caller (e.g. a form) can show the error
  const create = async (data) => {
    await api.post(basePath, data);
    await reload();
  };

  const update = async (id, data) => {
    await api.patch(`${basePath}/${id}`, data);
    await reload();
  };

  const remove = async (id) => {
    await api.delete(`${basePath}/${id}`);
    await reload();
  };

  return { items, loading, error, reload, create, update, remove };
}

export default useResource;
