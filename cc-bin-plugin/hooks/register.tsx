import type { On } from 'claude-code'

const LABELS: Record<string, string> = {
  an: 'Anthropic',
  zp: '智谱',
  ds: 'DeepSeek',
  mm: 'MiniMax',
  'mm-api': 'MiniMax（API）',
  mimo: 'MiMo',
  'mimo-api': 'MiMo（API）',
}

export function register(on: On) {
  let busy = false
  let message = ''
  let selected: string | undefined
  let available: { value: string; label: string }[] = []
  // Keep the native key before our first switch clears the working auth fields.
  // Only sent to ccs's child environment; never included in UI, logs or arguments.
  let nativeKey: string | undefined

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'provider',
      description: 'Switch cc-bin Provider (global settings)',
    })
    return next(e)
  })

  on('command.run', { command: 'provider' }, async ($, e) => {
    if (!e.presentation.isFullscreen) {
      return { text: '/provider requires Claude Code fullscreen terminal mode.' }
    }

    if (!busy) {
      message = ''
      try {
        nativeKey ??= (await $.env.get('ANTHROPIC_API_KEY')) ?? ''
        const result = await $.process.run(['ccs', '--list'], {
          timeoutMs: 10000, env: { ANTHROPIC_API_KEY: nativeKey },
        })
        if (result.exitCode !== 0 || result.isStdoutTruncated) throw new Error()
        const ids: unknown = JSON.parse(result.stdout)
        if (!Array.isArray(ids) || !ids.every(id =>
          typeof id === 'string' && Object.hasOwn(LABELS, id),
        ) || new Set(ids).size !== ids.length) throw new Error()
        available = ids.map(value => ({ value, label: LABELS[value] }))
      } catch {
        return { text: 'Could not load Providers. Check that the updated cc-bin ccs is on PATH and retry.' }
      }
      if (!available.length) {
        return { text: 'No Provider API Key found. Export a supported Provider API Key before starting Claude Code.' }
      }
      if (!available.some(provider => provider.value === selected)) selected = undefined
    }
    try {
      const placed = await $.ui.open({
        id: 'provider',
        title: 'Select Provider',
        focus: true,
        closeOnEscape: true,
        rows: 12,
      })
      return placed.isPlaced
        ? {}
        : { text: 'Could not open the Provider picker. Enlarge the terminal and retry.' }
    } catch {
      return { text: 'Could not open the Provider picker. Retry /provider in fullscreen mode.' }
    }
  })

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== 'provider' || e.surface !== 'terminal') return next(e)
    const { Box, Text, Select } = await $.ui.resolve(e)

    return (
      <Box flexDirection="column">
        <Text>Updates ~/.claude/settings.json (global)</Text>
        {busy ? <Text>Switching Provider…</Text> : (
          <Select
            key="provider"
            label="Select Provider"
            options={available}
            value={selected}
            autoFocus
            onSelect={async value => {
              const provider = available.find(item => item.value === value)
              if (busy || !provider) return
              busy = true
              message = ''
              $.ui.invalidate('ui.render')

              const result = await $.process.run(['ccs', provider.value], {
                timeoutMs: 10000, env: { ANTHROPIC_API_KEY: nativeKey ?? '' },
              }).catch(() => undefined)
              busy = false
              // Subprocess output and exception messages may contain credentials.
              if (!result) {
                message = 'Could not run ccs. Check cc-bin is on PATH and retry.'
              } else if (result.exitCode !== 0) {
                message = `Could not switch to ${provider.label}. Check cc-bin environment variables and ~/.claude permissions.`
              } else {
                selected = provider.value
                message = `✓ Provider switched to ${provider.label}`
                $.ui.log(message)
              }
              $.ui.invalidate('ui.render')
              if (result?.exitCode !== 0) return
              try {
                await $.ui.close({ id: 'provider' })
              } catch {
                // Switching already succeeded; the message stays visible until Esc.
              }
            }}
          />
        )}
        {message ? <Text>{message}</Text> : null}
      </Box>
    )
  })
}
