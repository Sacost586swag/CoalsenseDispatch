import { authError, handleAuth, readConfig } from "../../../../features/auth/server.ts";

async function handler(request: Request, context: { params: Promise<{ action: string }> }) {
  try {
    const config = readConfig();
    const { action } = await context.params;
    return await handleAuth(request, action, config);
  } catch {
    return authError(503);
  }
}
export { handler as GET, handler as POST };
