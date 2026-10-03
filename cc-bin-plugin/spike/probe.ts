// Research probe only. run.py substitutes the two path/URL constants in a
// temporary plugin. No /provider command or Provider switching is implemented.
export function register(on) {
  let envReads = 0
  let httpCalls = 0
  let completions = 0
  let steps = 0

  on('env.get', { name: 'ANTHROPIC_BASE_URL' }, () => {
    envReads++
    return { value: __REPLACEMENT_URL__ }
  })
  on('env.get', { name: 'ANTHROPIC_API_KEY' }, () => {
    envReads++
    return { value: 'spike-replacement-placeholder' }
  })
  on('http.fetch', ($, e, next) => {
    httpCalls++
    return next(e)
  })
  on('model.complete', ($, e, next) => {
    completions++
    return next(e)
  })
  on('turn.step', async function* ($, e, next) {
    steps++
    // model is documented. baseURL/apiKey are deliberately unsupported fields
    // under investigation: the real engine must prove whether it consumes them.
    return yield* next({
      ...e,
      model: 'spike-rewritten-model',
      baseURL: __REPLACEMENT_URL__,
      apiKey: 'spike-replacement-placeholder',
    })
  })
  on('turn.complete', async ($, e, next) => {
    await $.fs.write(
      __COUNTS_PATH__,
      JSON.stringify({ envReads, httpCalls, completions, steps }),
    )
    return next(e)
  })
}
