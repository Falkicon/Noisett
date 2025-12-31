/**
 * Build script for Noisett Figma Plugin
 *
 * Bundles TypeScript code and inlines UI JS into HTML.
 */

const esbuild = require("esbuild");
const fs = require("fs");
const path = require("path");

async function build() {
  // Ensure dist directory exists
  const distDir = path.join(__dirname, "dist");
  if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir);
  }

  // Build main plugin code
  await esbuild.build({
    entryPoints: ["src/code.ts"],
    bundle: true,
    outfile: "dist/code.js",
    format: "iife",
    target: "es2020",
    minify: true,
  });
  console.log("✓ Built code.js");

  // Build UI code
  const uiResult = await esbuild.build({
    entryPoints: ["src/ui.ts"],
    bundle: true,
    write: false,
    format: "iife",
    target: "es2020",
    minify: true,
  });
  const uiJs = uiResult.outputFiles[0].text;
  console.log("✓ Built UI JS");

  // Read HTML template and inline the JS
  const htmlTemplate = fs.readFileSync("src/ui.html", "utf8");
  const htmlWithJs = htmlTemplate.replace(
    "<!-- INLINE_SCRIPT -->",
    `<script>${uiJs}</script>`
  );

  fs.writeFileSync("dist/ui.html", htmlWithJs);
  console.log("✓ Built ui.html with inlined script");

  console.log("\n🎉 Build complete!");
}

build().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
