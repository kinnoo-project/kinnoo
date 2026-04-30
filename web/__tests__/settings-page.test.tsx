import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import SettingsPage from "../app/(auth)/settings/page";

afterEach(() => {
  cleanup();
});

describe("Settings page", () => {
  it("renders centered settings heading", () => {
    render(<SettingsPage />);

    expect(screen.getByRole("heading", { name: "Settings" })).toBeTruthy();
  });
});
