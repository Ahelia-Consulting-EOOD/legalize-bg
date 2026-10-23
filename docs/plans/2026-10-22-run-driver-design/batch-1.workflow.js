export const meta = {
  name: 'structure-map-batch',
  description: 'Label one round of the structure map for a batch of acts: one labeller call per call file',
  phases: [{ title: 'Label', detail: 'one labeller call per call file listed by reading/run.py dispatch --json' }],
}
// args: the JSON list that `reading/run.py dispatch SLUGS --round R --json --max N` prints:
//   [{slug, round, name, tasks, call_file, answer_file, prompt}, ...]
// The script has no file access, so the session runs dispatch first and passes its output here. Each call reads
// its call file and writes its answer file itself; the run folder is the record, and `collect` splits the answers.
// Resume: the same args with `resumeFromRunId` replay finished calls; a stopped call is listed again by dispatch.
phase('Label')
const calls = Array.isArray(args) ? args : []
if (!calls.length) { log('no calls to run'); return { calls: 0 } }
log(`${calls.length} calls, ${calls.reduce((n, c) => n + c.tasks, 0)} tasks`)
const results = await pipeline(
  calls,
  c => agent(c.prompt, { agentType: 'labeller', model: 'opus', label: `${c.slug.slice(0, 24)} r${c.round} ${c.name.slice(13)}`, phase: 'Label' }),
)
const done = results.filter(Boolean).length
log(`${done} of ${calls.length} calls replied`)
return { calls: calls.length, replied: done, failed: calls.length - done }
