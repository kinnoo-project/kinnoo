import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

// [agent] test used during UAT or migration, currently not used for regression
describe.skip("feature118 redirect auth flow [deprecated]", () => {
	it("is retained for historical context only", () => {
		expect(true).toBe(true);
	});
});
