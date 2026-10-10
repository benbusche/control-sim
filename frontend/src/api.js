let pendingCommands = Promise.resolve();

export async function getState() {
  const response = await fetch("/api/state");
  if (!response.ok) throw new Error("Could not read simulation state");
  return response.json();
}

export function sendCommand(command) {
  const request = pendingCommands.then(async () => {
    const response = await fetch("/api/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Request failed");
    return result;
  });

  // Keep later commands working if one request fails.
  pendingCommands = request.catch(() => {});
  return request;
}
