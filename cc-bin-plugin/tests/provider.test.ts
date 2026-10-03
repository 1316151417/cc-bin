import type { CommandRunInput, On, ProcessRunInit, ProcessRunResult, SessionStartInput } from 'claude-code'
import { expect, test } from 'claude-code/testing'
import type { Engine, MountTarget } from 'claude-code/testing'

const SESSION: SessionStartInput = { surface: 'terminal', isInteractive: true, cwd: '/work' }
const COMMAND: CommandRunInput = {
  command: 'provider', args: '', origin: { kind: 'composer' },
  presentation: { isFullscreen: true, columns: 160 },
}
const PANE: MountTarget<'terminal', 'Pane'> = {
  plugin: 'cc-bin-provider', component: 'Pane', surface: 'terminal', requestId: 'provider',
  viewport: { columns: 160, rows: 40, isFullscreen: true },
  props: {
    title: 'Select Provider', isFocused: true, bodyColumns: 80, placement: 'dock',
    scroll: { offset: 0, bodyRows: 12 }, view: {},
  },
}
const OK: ProcessRunResult = {
  exitCode: 0, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false,
}
const PROVIDERS = [
  ['an', 'Anthropic'], ['zp', '智谱'], ['ds', 'DeepSeek'],
  ['mm', 'MiniMax'], ['mm-api', 'MiniMax（API）'],
  ['mimo', 'MiMo'], ['mimo-api', 'MiMo（API）'],
]

function world(on: On, ids = PROVIDERS.map(([id]) => id)) {
  const runs: string[][] = []
  const runOptions: (ProcessRunInit | undefined)[] = []
  const listings: (ProcessRunInit | undefined)[] = []
  const logs: string[] = []
  const registered: string[] = []
  const closed: string[] = []
  const reads: string[] = []
  let nativeKey = 'dummy-native-key'
  let result = OK
  let listing = { ...OK, stdout: JSON.stringify(ids) }
  let denied = false
  let placed = true

  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('env.get', ($, e) => { reads.push(e.name); return { value: nativeKey } })
  on('command.register', ($, e) => {
    registered.push(e.name)
    return { value: { command: e.name } }
  })
  on('process.run', ($, e) => {
    expect(e.argv[0]).toBe('ccs')
    if (e.argv[1] === '--list') {
      listings.push(e.init)
      return { value: listing }
    }
    runs.push([...e.argv])
    runOptions.push(e.init)
    return denied ? { deny: 'secret-from-process-error' } : { value: result }
  })
  on('ui.open', () => ({ value: placed ? { isPlaced: true } : { isPlaced: false, reason: 'No room' } }))
  on('ui.close', ($, e) => { closed.push(e.id); return { value: undefined } })
  on('ui.log', ($, e) => { logs.push(e.text); return { value: undefined } })
  on('ui.focus', () => ({}))

  return {
    runs, runOptions, listings, logs, registered, closed, reads,
    fail() { result = { ...OK, exitCode: 1, stdout: 'secret-stdout', stderr: 'secret-stderr' } },
    deny() { denied = true },
    succeed() { result = OK; denied = false },
    noRoom() { placed = false },
    list(value: Partial<ProcessRunResult>) { listing = { ...listing, ...value } },
    clearWorkingKey() { nativeKey = '' },
  }
}

async function open($: Engine) {
  await $.session.start(SESSION)
  expect(await $.command.run(COMMAND)).toEqual({})
  return $.ui.mount(PANE)
}

test('official Select dispatches all supported aliases and reports success', async ($, on) => {
  const observed = world(on)
  const ui = await open($)
  expect(observed.registered).toEqual(['provider'])

  for (const [value, label] of PROVIDERS) {
    expect(JSON.stringify(await ui.drawn())).toContain(label)
    await ui.select({ key: 'provider', value })
    expect(observed.runs[observed.runs.length - 1]).toEqual(['ccs', value])
    expect(observed.logs[observed.logs.length - 1]).toBe(`✓ Provider switched to ${label}`)
    expect(observed.closed[observed.closed.length - 1]).toBe('provider')
    await $.command.run(COMMAND)
  }
  expect(observed.runs.length).toBe(7)
  expect(JSON.stringify(await ui.drawn())).not.toContain('OpenAI')
  expect(JSON.stringify(await ui.drawn())).not.toContain('dummy-native-key')
  await ui.unmount()
})

test('a nonzero ccs exit shows a safe error and permits retry', async ($, on) => {
  const observed = world(on)
  observed.fail()
  const ui = await open($)
  await ui.select({ key: 'provider', value: 'zp' })
  const drawing = JSON.stringify(await ui.drawn())
  expect(drawing).toContain('Could not switch to 智谱')
  expect(drawing).not.toContain('secret-')
  expect(observed.logs).toEqual([])
  expect(observed.closed).toEqual([])

  observed.succeed()
  await ui.select({ key: 'provider', value: 'ds' })
  expect(observed.logs).toEqual(['✓ Provider switched to DeepSeek'])
  await ui.unmount()
})

test('missing or denied ccs does not expose the underlying error', async ($, on) => {
  const observed = world(on)
  observed.deny()
  const ui = await open($)
  await ui.select({ key: 'provider', value: 'mm' })
  const drawing = JSON.stringify(await ui.drawn())
  expect(drawing).toContain('Could not run ccs')
  expect(drawing).not.toContain('secret-')
  expect(observed.logs).toEqual([])
  observed.succeed()
  await ui.select({ key: 'provider', value: 'mm' })
  expect(observed.logs).toEqual(['✓ Provider switched to MiniMax'])
  await ui.unmount()
})

test('opening and dismissing only performs read-only discovery', async ($, on) => {
  const observed = world(on)
  const ui = await open($)
  await ui.unmount()
  expect(observed.listings.length).toBe(1)
  expect(observed.runs).toEqual([])
  expect(observed.logs).toEqual([])
})

test('headless or non-fullscreen commands explain the requirement', async ($, on) => {
  const observed = world(on)
  await $.session.start(SESSION)
  expect(await $.command.run({ ...COMMAND, presentation: { isFullscreen: false, columns: 80 } }))
    .toEqual({ text: '/provider requires Claude Code fullscreen terminal mode.' })
  expect(observed.runs).toEqual([])
  expect(observed.listings).toEqual([])
})

test('unavailable UI placement is reported without switching', async ($, on) => {
  const observed = world(on)
  observed.noRoom()
  await $.session.start(SESSION)
  expect(await $.command.run(COMMAND)).toEqual({
    text: 'Could not open the Provider picker. Enlarge the terminal and retry.',
  })
  expect(observed.runs).toEqual([])
})

test('cc-bin discovery controls the menu and Zhipu appears only once', async ($, on) => {
  const observed = world(on, ['zp'])
  const ui = await open($)
  const drawing = JSON.stringify(await ui.drawn())
  expect(drawing).toContain('智谱')
  expect(drawing).not.toContain('DeepSeek')
  expect(drawing).not.toContain('MiniMax')
  expect(drawing).not.toContain('MiMo')
  expect(drawing).not.toContain('Coding Plan')
  expect(observed.reads).toEqual(['ANTHROPIC_API_KEY'])
  await ui.unmount()
})

test('no configured API Keys reports an empty state without switching', async ($, on) => {
  const observed = world(on, [])
  await $.session.start(SESSION)
  expect((await $.command.run(COMMAND)).text).toContain('No Provider API Key found')
  expect(observed.runs).toEqual([])
})

test('old ccs and malformed discovery never echo output or switch', async ($, on) => {
  const observed = world(on)
  await $.session.start(SESSION)
  for (const listing of [
    { exitCode: 1, stdout: 'secret-old-ccs', stderr: 'secret-stderr' },
    { exitCode: 0, stdout: 'secret-not-json' },
    { stdout: '{"secret-api-key":"dummy"}' },
    { stdout: '["openai"]' },
    { stdout: '["__proto__"]' },
    { stdout: '["ds","ds"]' },
    { stdout: '["ds"]', isStdoutTruncated: true },
  ]) {
    observed.list(listing)
    const result = await $.command.run(COMMAND)
    expect(result.text).toContain('Could not load Providers')
    expect(JSON.stringify(result)).not.toContain('secret')
  }
  expect(observed.runs).toEqual([])
  expect(observed.logs).toEqual([])
})

test('native credentials survive a switch that clears the working API Key', async ($, on) => {
  const observed = world(on)
  const ui = await open($)
  await ui.select({ key: 'provider', value: 'ds' })
  observed.clearWorkingKey()
  await $.command.run(COMMAND)
  await ui.select({ key: 'provider', value: 'an' })
  expect(observed.reads).toEqual(['ANTHROPIC_API_KEY'])
  expect(observed.runOptions[1]?.env).toEqual({ ANTHROPIC_API_KEY: 'dummy-native-key' })
  expect(observed.listings[1]?.env).toEqual({ ANTHROPIC_API_KEY: 'dummy-native-key' })
  expect(JSON.stringify(observed.logs)).not.toContain('dummy-native-key')
  await ui.unmount()
})
