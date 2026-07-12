export async function isTauri(): Promise<boolean> {
	try {
		const { getName } = await import("@tauri-apps/api/app");
		await getName();
		return true;
	} catch {
		return false;
	}
}
