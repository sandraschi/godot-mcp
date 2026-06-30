import { create } from "zustand";

interface AppState {
	connectionStatus: "connected" | "disconnected" | "connecting";
	serverVersion: string;
	godotAvailable: boolean;
	tauriAvailable: boolean;
	setConnectionStatus: (status: AppState["connectionStatus"]) => void;
	setServerVersion: (version: string) => void;
	setGodotAvailable: (available: boolean) => void;
	setTauriAvailable: (available: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
	connectionStatus: "connecting",
	serverVersion: "",
	godotAvailable: false,
	tauriAvailable: false,
	setConnectionStatus: (status) => set({ connectionStatus: status }),
	setServerVersion: (version) => set({ serverVersion: version }),
	setGodotAvailable: (available) => set({ godotAvailable: available }),
	setTauriAvailable: (available) => set({ tauriAvailable: available }),
}));
