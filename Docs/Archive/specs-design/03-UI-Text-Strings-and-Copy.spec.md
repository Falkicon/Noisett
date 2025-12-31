# UI Text Strings & Copy

All user-facing text strings for the Brand Asset Generator. Use this as the source of truth for implementation.

---

## App Name & Branding

| Key | String |
| --- | --- |
| [`app.name`](http://app.name) | Brand Asset Generator |
| [`app.name](http://app.name).short` | Asset Generator |
| `app.tagline` | Generate on-brand illustrations in seconds |

---

## Header & Navigation

| Key | String |
| --- | --- |
| `nav.signOut` | Sign out |
| `nav.settings` | Settings |
| [`nav.help`](http://nav.help) | Help |

---

## Generate Tab (Input)

| Key | String |
| --- | --- |
| `input.label` | Describe what you need |
| `input.placeholder` | e.g., "A person collaborating with AI on a creative project" |
| `input.charCount` | {count}/500 |
| `input.tip` | 💡 **Tip:** Be specific about the subject, composition, and style you want. |

### Asset Type Selector (v2.0+)

| Key | String |
| --- | --- |
| `assetType.label` | Asset type |
| `assetType.icons` | Icons (Fluent 2) |
| `assetType.product` | Product Illustrations |
| `assetType.logo` | Logo Illustrations |
| `assetType.premium` | Premium Illustrations |

### Model Selector (v2.0+)

| Key | String |
| --- | --- |
| `model.label` | Model |
| `model.hidream` | HiDream |
| `model.hidream.badge` | ✓ Commercial OK |
| `model.flux` | FLUX |
| `model.flux.badge` | ⚠ Reference only |
| [`model.sd](http://model.sd)35` | SD 3.5 |
| [`model.sd](http://model.sd)35.badge` | ⚠ Check license |

### Quality Selector (v2.1+)

| Key | String |
| --- | --- |
| `quality.label` | Quality |
| `quality.draft` | Draft |
| `quality.draft.time` | ~10 sec |
| `quality.standard` | Standard |
| `quality.standard.time` | ~25 sec |
| `quality.high` | High |
| `quality.high.time` | ~45 sec |
| `quality.ultra` | Ultra |
| `quality.ultra.time` | ~90 sec |

---

## Buttons

| Key | String | Context |
| --- | --- | --- |
| `button.generate` | Generate | Primary action, initial |
| `button.generate.count` | Generate ({count} images) | With image count |
| `button.generateMore` | Generate More | After results shown |
| `button.newPrompt` | New Prompt | Start over |
| [`button.download`](http://button.download) | Download | On image card |
| `button.downloadAll` | Download All | Batch download (v2.1+) |
| `button.insert` | Insert | Figma plugin |
| `button.insertToCanvas` | Insert to Canvas | Figma plugin (expanded) |
| `button.tryAgain` | Try Again | After error |
| `button.editPrompt` | Edit Prompt | After error |
| `button.cancel` | Cancel | During generation |
| `button.signIn` | Sign in | Auth screen |
| `button.signInWithSSO` | Sign in with SSO | Auth screen |
| `button.signOut` | Sign out | Settings |

---

## Loading & Progress

| Key | String |
| --- | --- |
| `loading.generating` | Generating... |
| `loading.creating` | Creating {count} variations |
| `loading.time` | This takes about {seconds} seconds |
| `loading.progress` | {percent}% complete |
| `loading.almostDone` | Almost done... |

---

## Results

| Key | String |
| --- | --- |
| `results.title` | Results |
| `results.yourPrompt` | Your prompt: |
| `results.variation` | Variation {n} |
| `results.inserted` | ✓ Inserted to canvas |
| `results.downloaded` | ✓ Downloaded |

---

## History (v2.1+)

| Key | String |
| --- | --- |
| `history.title` | History |
| `history.recent` | Recent Generations |
| `history.empty` | No generations yet |
| `history.empty.hint` | Your generations will appear here |
| [`history.timeAgo.now`](http://history.timeAgo.now) | Just now |
| `history.timeAgo.minutes` | {n} min ago |
| `history.timeAgo.hours` | {n} hours ago |
| `history.timeAgo.yesterday` | Yesterday |
| `history.timeAgo.days` | {n} days ago |

---

## Favorites (v2.1+)

| Key | String |
| --- | --- |
| `favorites.title` | Favorites |
| `favorites.empty` | No favorites yet |
| `favorites.empty.hint` | Star images you like to find them here |
| `favorites.add` | Add to favorites |
| `favorites.remove` | Remove from favorites |

---

## Errors

| Key | String |
| --- | --- |
| `error.generic` | Something went wrong. Please try again. |
| `error.generation` | Generation failed |
| `error.generation.detail` | We couldn't generate your images. This sometimes happens with complex prompts. |
| [`error.network`](http://error.network) | Can't connect |
| [`error.network](http://error.network).detail` | Check your internet connection and try again. |
| `error.timeout` | Request timed out |
| `error.timeout.detail` | The server took too long to respond. Please try again. |
| `error.unauthorized` | Access denied |
| `error.unauthorized.detail` | You don't have permission to use this tool. Contact your admin. |
| `error.sessionExpired` | Session expired |
| `error.sessionExpired.detail` | Your session has expired. Please sign in again. |

---

## Authentication

| Key | String |
| --- | --- |
| `auth.signIn.title` | Sign in to continue |
| `auth.signIn.hint` | Use your work account to access Brand Asset Generator |
| `auth.signedInAs` | Signed in as {email} |
| `auth.deviceCode.title` | Sign in on the web |
| `auth.deviceCode.instruction` | Go to {url} and enter this code: |
| `auth.deviceCode.code` | {code} |
| `auth.deviceCode.waiting` | Waiting for sign in... |

---

## Settings

| Key | String |
| --- | --- |
| `settings.title` | Settings |
| `settings.account` | Account |
| `settings.defaults` | Defaults |
| `settings.defaultAssetType` | Default asset type |
| `settings.defaultQuality` | Default quality |
| `settings.defaultModel` | Default model |
| `settings.about` | About |
| `settings.version` | Version {version} |
| [`settings.docs`](http://settings.docs) | View Documentation |

---

## Licensing Warnings (v2.0+)

| Key | String |
| --- | --- |
| `license.warning.title` | Licensing notice |
| `license.warning.flux` | FLUX is for **reference use only** unless you have a commercial license. Generated images should not be used directly in product. |
| `license.warning.acknowledge` | I understand |
| `license.badge.commercial` | ✓ Commercial OK |
| `license.badge.referenceOnly` | ⚠ Reference only |
| `license.learnMore` | Learn more about licensing |

---

## Tooltips & Hints

| Key | String |
| --- | --- |
| `tooltip.assetType` | Different asset types are optimized for different use cases |
| `tooltip.quality.draft` | Fast but lower quality. Good for ideation. |
| `tooltip.quality.standard` | Balanced quality and speed. Good for most uses. |
| `tooltip.quality.high` | Higher quality with upscaling. Good for final assets. |
| `tooltip.model` | Different models have different strengths and licensing terms |
| [`tooltip.download`](http://tooltip.download) | Download as PNG (1024×1024) |
| `tooltip.insert` | Insert this image onto your Figma canvas |

---

## Accessibility Labels

| Key | String |
| --- | --- |
| `a11y.promptInput` | Prompt input field |
| `a11y.generateButton` | Generate images button |
| `a11y.resultImage` | Generated image {n} of {total} |
| `a11y.downloadButton` | Download image {n} |
| `a11y.insertButton` | Insert image {n} to canvas |
| `a11y.progress` | Generation progress: {percent} percent |
| `a11y.loading` | Loading, please wait |

---

## Confirmation Messages

| Key | String |
| --- | --- |
| `confirm.cancel` | Cancel generation? |
| `confirm.cancel.detail` | Your current generation will be stopped. |
| `confirm.signOut` | Sign out? |
| `confirm.signOut.detail` | You'll need to sign in again to use the tool. |