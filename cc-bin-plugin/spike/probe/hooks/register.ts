import type { On } from 'claude-code'

// Research only. No settings writes, env.set, real credentials, or remote API.
export function register(on: On) {
  let target = ''
  const seen = { steps: 0, envReads: 0, httpFetches: 0, completions: 0 }

  on('session.start', async ($, e, next) => {
    target = (await $.env.get('CC_PROVIDER_SPIKE_TARGET_URL')) ?? ''
    await $.command.register({
      name: 'provider-spike',
      description: 'Read-only provider API capability probe',
    })
    return next(e)
  })

  on('command.run', { command: 'provider-spike' }, async ($) => ({
    text: JSON.stringify({ version: await $.session.version(), ...seen }),
  }))

  // This event intercepts calls to $.env.get, not the engine's process.env.
  on('env.get', { name: 'ANTHROPIC_BASE_URL' }, () => {
    seen.envReads += 1
    return { value: target }
  })

  on('http.fetch', ($, e, next) => {
    seen.httpFetches += 1
    return next(e)
  })

  on('model.complete', ($, e, next) => {
    seen.completions += 1
    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    seen.steps += 1
    // model is supported. Extra transport fields are deliberately supplied
    // to check whether core consumes them; none is a declared TurnStepInput.
    const attempted = {
      ...e,
      model: 'claude-haiku-4-5-20251001',
      baseURL: target,
      apiKey: 'spike-replacement-placeholder',
      env: {
        ANTHROPIC_BASE_URL: target,
        ANTHROPIC_API_KEY: 'spike-replacement-placeholder',
      },
    }
    return yield* next(attempted)
  })

  on('turn.complete', async ($, e, next) => {
    await $.ui.log(`provider-api-spike: ${JSON.stringify(seen)}`)
    return next(e)
  })
}
