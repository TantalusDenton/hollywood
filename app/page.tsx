'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Aperture,
  ArrowRight,
  Check,
  ChevronDown,
  ChevronRight,
  Clapperboard,
  Clock3,
  Film,
  Frame,
  Layers3,
  LayoutDashboard,
  LoaderCircle,
  MoreHorizontal,
  Music2,
  PanelRight,
  Play,
  Plus,
  Settings2,
  Sparkles,
  WandSparkles,
  type LucideIcon,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const stages = [
  { label: 'Story analysis', detail: 'World & style bible', state: 'done' },
  { label: 'Characters', detail: '3 references approved', state: 'done' },
  { label: 'Scene plan', detail: '4 narrative sequences', state: 'active' },
  { label: 'Shot design', detail: 'Waiting for scene plan', state: 'pending' },
  { label: 'Keyframes', detail: 'Waiting for shot design', state: 'pending' },
  { label: 'Video clips', detail: 'Waiting for keyframes', state: 'pending' },
  { label: 'Final assembly', detail: 'Waiting for clips', state: 'pending' },
];

const scenes = [
  { number: '01', title: 'The signal in the dust', shots: 4, duration: '00:34', status: 'ready' },
  { number: '02', title: 'A city that remembers', shots: 5, duration: '00:42', status: 'active' },
  { number: '03', title: 'The impossible crossing', shots: 3, duration: '00:25', status: 'pending' },
  { number: '04', title: 'First light', shots: 4, duration: '00:31', status: 'pending' },
];

const characters = [
  { initials: 'MA', name: 'Mara Voss', role: 'Lead archaeologist', color: 'from-orange-300 via-amber-200 to-stone-700' },
  { initials: 'EL', name: 'Eli Voss', role: 'Field pilot', color: 'from-cyan-200 via-slate-400 to-slate-900' },
  { initials: 'AV', name: 'The Archive', role: 'City intelligence', color: 'from-violet-200 via-indigo-500 to-slate-900' },
];

const navigationItems: { value: string; label: string; icon: LucideIcon }[] = [
  { value: 'story', label: 'Story', icon: Sparkles },
  { value: 'characters', label: 'Characters', icon: Aperture },
  { value: 'scenes', label: 'Scenes', icon: Layers3 },
  { value: 'shots', label: 'Shots', icon: Frame },
  { value: 'keyframes', label: 'Keyframes', icon: LayoutDashboard },
  { value: 'videos', label: 'Videos', icon: Film },
  { value: 'timeline', label: 'Timeline', icon: Clock3 },
];

type StudioMode = 'new' | 'working';

type WebMCPContext = {
  registerTool: (tool: {
    name: string;
    title: string;
    description: string;
    inputSchema: object;
    annotations: { readOnlyHint: boolean; untrustedContentHint: boolean };
    execute: (input: unknown) => Promise<unknown>;
  }, options: { signal: AbortSignal }) => void | Promise<void>;
};

function StageDot({ state }: { state: string }) {
  if (state === 'done') {
    return <span className="flex size-5 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300"><Check className="size-3" /></span>;
  }
  if (state === 'active') {
    return <span className="relative flex size-5 items-center justify-center"><span className="absolute size-5 animate-ping rounded-full bg-amber-300/25" /><span className="relative size-2 rounded-full bg-amber-200" /></span>;
  }
  return <span className="size-2 rounded-full bg-white/20" />;
}

function FilmStill({ kind, label }: { kind: 'start' | 'video' | 'end'; label: string }) {
  const background = kind === 'start'
    ? 'from-[#27323d] via-[#b2774c] to-[#edc78c]'
    : kind === 'end'
      ? 'from-[#111b2c] via-[#2e4c63] to-[#d9a35b]'
      : 'from-[#1d2732] via-[#57624e] to-[#d2a264]';
  return (
    <div className={`group relative aspect-video overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br ${background}`}>
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/65 to-transparent" />
      <div className="absolute -left-8 top-5 size-32 rounded-full border-[18px] border-white/10 blur-[1px]" />
      <div className="absolute left-[42%] top-[25%] h-[57%] w-[16%] rounded-[48%_48%_16%_16%] bg-black/35 shadow-[0_8px_0_11px_rgb(0_0_0/18%)]" />
      <div className="absolute bottom-2.5 left-3 text-[10px] font-medium uppercase tracking-[0.16em] text-white/70">{label}</div>
      {kind === 'video' && <span className="absolute left-1/2 top-1/2 flex size-10 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/30 bg-black/30 text-white backdrop-blur-sm"><Play className="ml-0.5 size-4 fill-current" /></span>}
    </div>
  );
}

export default function Home() {
  const [mode, setMode] = useState<StudioMode>('new');
  const [prompt, setPrompt] = useState('A field archaeologist discovers a buried city that wakes up when the desert lights turn blue.');
  const [directorMode, setDirectorMode] = useState(true);
  const [activeTab, setActiveTab] = useState('story');
  const [expanded, setExpanded] = useState('02');
  const [isCreating, setIsCreating] = useState(false);
  const [notice, setNotice] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [projectTitle, setProjectTitle] = useState('Untitled film');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioSliceSeconds, setAudioSliceSeconds] = useState(4);
  const [audioSliceCount, setAudioSliceCount] = useState<number | null>(null);
  const startProjectRef = useRef<(moviePrompt: string, useDirectorMode: boolean) => Promise<boolean>>(async () => false);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const wordCount = useMemo(() => prompt.trim() ? prompt.trim().split(/\s+/).length : 0, [prompt]);

  async function sliceUploadedAudio(file: File) {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api';
    const body = new FormData();
    body.append('file', file);
    body.append('slice_seconds', String(audioSliceSeconds));
    const response = await fetch(`${apiUrl}/audio/slice`, { method: 'POST', body });
    if (!response.ok) throw new Error('Audio slicing failed');
    const result = await response.json() as { fragments: unknown[] };
    setAudioSliceCount(result.fragments.length);
    return result.fragments.length;
  }

  async function startProject(moviePrompt: string, useDirectorMode: boolean): Promise<boolean> {
    if (!moviePrompt.trim()) return false;
    setIsCreating(true);
    setNotice('Preparing your project…');
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api';
    try {
      const response = await fetch(`${apiUrl}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ original_prompt: moviePrompt, generation_settings: { director_mode: useDirectorMode } }),
      });
      if (!response.ok) throw new Error('Project service unavailable');
      const project = await response.json() as { id: string; title: string };
      setProjectId(project.id);
      setProjectTitle(project.title);
      setMode('working');
      setNotice('Project created — the story team is reading your brief.');
      if (audioFile) {
        setNotice(`Slicing ${audioFile.name} into ${audioSliceSeconds}-second cues…`);
        try {
          const cueCount = await sliceUploadedAudio(audioFile);
          setNotice(`${cueCount} audio cues are ready for your timeline.`);
        } catch {
          setNotice('Project created, but the audio file could not be sliced.');
        }
      }
      return true;
    } catch {
      setNotice('Hollywood API is unavailable. Start the backend, then try again.');
      return false;
    } finally {
      setIsCreating(false);
    }
  }

  startProjectRef.current = startProject;

  useEffect(() => {
    if (!projectId) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api';
    const events = new EventSource(`${apiUrl}/projects/${projectId}/events`);
    events.addEventListener('pipeline', (rawEvent) => {
      const event = JSON.parse((rawEvent as MessageEvent<string>).data) as { message?: string; status?: string; payload?: { title?: string } };
      if (event.message) setNotice(event.message);
      if (event.payload?.title) setProjectTitle(event.payload.title);
      if (event.status === 'completed' || event.status === 'failed') window.setTimeout(() => setNotice(''), 5000);
    });
    return () => events.close();
  }, [projectId]);

  useEffect(() => {
    const modelContext = (document as Document & { modelContext?: WebMCPContext }).modelContext;
    if (!modelContext?.registerTool) return;
    const lifecycle = new AbortController();
    const tool = {
      name: 'create_movie_project',
      title: 'Create a Hollywood movie project',
      description: 'Create a movie project from a story prompt and open the project workspace.',
      inputSchema: {
        type: 'object',
        properties: {
          prompt: { type: 'string', minLength: 1, description: 'The movie or story prompt.' },
          directorMode: { type: 'boolean', description: 'Pause the workflow at creative approval checkpoints.' },
        },
        required: ['prompt'],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      async execute(input: unknown) {
        if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Expected a movie project object.');
        const candidate = input as { prompt?: unknown; directorMode?: unknown };
        if (typeof candidate.prompt !== 'string' || !candidate.prompt.trim()) throw new Error('prompt must be a non-empty string.');
        if (candidate.directorMode !== undefined && typeof candidate.directorMode !== 'boolean') throw new Error('directorMode must be a boolean when supplied.');
        const requestedDirectorMode = candidate.directorMode ?? true;
        setPrompt(candidate.prompt.trim());
        setDirectorMode(requestedDirectorMode);
        const created = await startProjectRef.current(candidate.prompt.trim(), requestedDirectorMode);
        if (!created) throw new Error('Hollywood API is unavailable.');
        return { status: 'workspace_opened', directorMode: requestedDirectorMode };
      },
    };
    try {
      void Promise.resolve(modelContext.registerTool(tool, { signal: lifecycle.signal })).catch(() => undefined);
    } catch {
      // WebMCP is optional outside supporting browsers.
    }
    return () => lifecycle.abort();
  }, []);

  async function createMovie() {
    await startProject(prompt, directorMode);
  }

  if (mode === 'new') {
    return (
      <main className="min-h-screen bg-[#0a0d12] text-white selection:bg-amber-200/30">
        <div className="cinema-noise pointer-events-none fixed inset-0 opacity-40" />
        <header className="relative mx-auto flex max-w-[1440px] items-center justify-between px-6 py-6 lg:px-10">
          <Brand />
          <div className="flex items-center gap-3 text-sm text-white/55">
            <span className="hidden sm:inline">Director&apos;s workspace</span>
            <span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_14px_#34d399]" />
          </div>
        </header>
        <section className="relative mx-auto flex min-h-[calc(100vh-88px)] max-w-[1040px] flex-col justify-center px-6 pb-24 lg:px-10">
          <div className="mb-7 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.22em] text-amber-200/75"><Sparkles className="size-3.5" /> AI film studio</div>
          <h1 className="max-w-3xl font-[family-name:var(--font-cinema)] text-5xl leading-[.95] tracking-[-0.05em] text-balance sm:text-7xl lg:text-8xl">What movie do you want to make?</h1>
          <p className="mt-6 max-w-2xl text-[1.05rem] leading-7 text-white/55">Start with the story. Hollywood turns your brief into a visual world, cast, scenes, shots, keyframes, and finished clips—one deliberate step at a time.</p>
          <div className="mt-10 overflow-hidden rounded-2xl border border-white/12 bg-white/[0.055] shadow-[0_30px_100px_-40px_rgba(0,0,0,.9)] backdrop-blur-xl">
            <textarea
              aria-label="Movie or story prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Describe the story, the people in it, and the feeling you want on screen…"
              className="min-h-44 w-full resize-none bg-transparent p-6 text-lg leading-7 text-white placeholder:text-white/25 focus:outline-none sm:p-8"
            />
            <div className="flex flex-col gap-3 border-t border-white/10 px-5 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
              <div className="flex flex-wrap items-center gap-3 text-sm text-white/60">
                <input ref={audioInputRef} type="file" accept="audio/mpeg,audio/wav,.mp3,.wav" className="hidden" onChange={(event) => setAudioFile(event.target.files?.[0] ?? null)} />
                <button type="button" onClick={() => audioInputRef.current?.click()} className="flex items-center gap-2 rounded-lg border border-white/12 bg-white/[.035] px-3 py-1.5 hover:bg-white/[.07]"><Music2 className="size-3.5 text-amber-100" />{audioFile ? audioFile.name : 'Add soundtrack (WAV or MP3)'}</button>
                {audioFile && <label className="flex items-center gap-2 text-xs text-white/48">Slice every <input aria-label="Audio slice duration" type="number" min="1" max="60" value={audioSliceSeconds} onChange={(event) => setAudioSliceSeconds(Math.max(1, Number(event.target.value) || 1))} className="w-11 rounded border border-white/15 bg-black/20 px-1.5 py-1 text-center text-white focus:outline-none" /> sec</label>}
              </div>
              <div className="flex items-center gap-4 text-xs text-white/45">
                <span>{wordCount} words</span>
                <span className="hidden h-3 w-px bg-white/15 sm:block" />
                <label className="flex cursor-pointer items-center gap-2 text-white/65"><Switch checked={directorMode} onCheckedChange={setDirectorMode} /><span>Director mode</span></label>
              </div>
              <Button onClick={createMovie} disabled={isCreating || !prompt.trim()} className="h-11 rounded-xl bg-amber-200 px-5 font-semibold text-[#15130f] hover:bg-amber-100">
                {isCreating ? <LoaderCircle className="size-4 animate-spin" /> : <Clapperboard className="size-4" />} {isCreating ? 'Creating' : 'Create movie'}
              </Button>
            </div>
          </div>
          {notice && <p role="status" className="mt-4 text-sm text-amber-100">{notice}</p>}
          <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-sm text-white/38"><span>Story → Character references → Scenes → Shots → Keyframes → Video</span><button onClick={() => setPrompt('A tender, sunlit coming-of-age story about two sisters restoring their grandmother’s abandoned seaside cinema.')} className="text-amber-100/80 hover:text-amber-100">Try an example <ArrowRight className="inline size-3.5" /></button></div>
        </section>
      </main>
    );
  }

  return (
    <TooltipProvider>
      <main className="min-h-screen bg-[#0a0d12] text-white selection:bg-amber-200/30">
        <div className="cinema-noise pointer-events-none fixed inset-0 opacity-30" />
        <header className="sticky top-0 z-20 flex h-[66px] items-center justify-between border-b border-white/10 bg-[#0a0d12]/90 px-4 backdrop-blur-xl lg:px-6">
          <div className="flex items-center gap-5"><Brand compact /><div className="hidden h-5 w-px bg-white/15 md:block" /><button className="hidden items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-white/70 hover:bg-white/5 md:flex"><span className="max-w-44 truncate">{projectTitle}</span><ChevronDown className="size-3.5 text-white/35" /></button></div>
          <div className="flex items-center gap-2"><span className="hidden rounded-full border border-amber-200/20 bg-amber-200/10 px-3 py-1 text-xs font-medium text-amber-100 sm:inline">Director mode</span><Tooltip><TooltipTrigger render={<button className="flex size-9 items-center justify-center rounded-lg text-white/60 hover:bg-white/6 hover:text-white" />}><Settings2 className="size-4" /></TooltipTrigger><TooltipContent>Project settings</TooltipContent></Tooltip><Button className="h-9 rounded-lg bg-amber-200 px-3 text-xs font-semibold text-[#17140f] hover:bg-amber-100"><Play className="size-3.5 fill-current" /> Assemble</Button></div>
        </header>

        {notice && <div role="status" className="fixed left-1/2 top-[78px] z-30 -translate-x-1/2 rounded-lg border border-amber-200/20 bg-[#1c1913] px-4 py-2 text-sm text-amber-100 shadow-xl">{notice}</div>}
        <div className="relative grid min-h-[calc(100vh-66px)] grid-cols-1 xl:grid-cols-[242px_minmax(0,1fr)_300px]">
          <aside className="hidden border-r border-white/10 bg-[#0c1016]/75 p-4 xl:block">
            <div className="mb-7 flex items-center justify-between px-2"><span className="text-xs font-semibold uppercase tracking-[0.16em] text-white/38">Projects</span><button className="rounded-md p-1 text-white/45 hover:bg-white/6 hover:text-white"><Plus className="size-4" /></button></div>
            <div className="rounded-xl border border-amber-200/15 bg-amber-200/[0.07] px-3 py-3"><div className="flex items-center gap-2 text-sm font-medium text-white"><span className="flex size-6 items-center justify-center rounded-md bg-amber-200 text-[#16130e]"><Film className="size-3.5" /></span><span className="truncate">{projectTitle}</span></div><div className="mt-2 pl-8 text-xs text-amber-100/70">In development</div></div>
            <nav className="mt-7 space-y-1" aria-label="Project areas">
              {navigationItems.map(({ value, label, icon: Icon }) => <button key={value} onClick={() => setActiveTab(value)} className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${activeTab === value ? 'bg-white/8 text-white' : 'text-white/48 hover:bg-white/5 hover:text-white/75'}`}><Icon className="size-4" />{label}</button>)}
            </nav>
            <div className="mt-10 rounded-xl border border-white/8 bg-white/[0.025] p-3.5"><div className="mb-3 flex items-center justify-between"><span className="text-xs font-medium text-white/70">Pipeline</span><span className="text-xs text-amber-100">43%</span></div><Progress value={43} className="[&_[data-slot=progress-indicator]]:bg-amber-200" /><p className="mt-3 text-xs leading-5 text-white/37">Scene planning is waiting for your review.</p></div>
          </aside>

          <section className="min-w-0 px-4 py-6 sm:px-7 lg:px-10 lg:py-8">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="gap-6">
              <div className="flex flex-wrap items-start justify-between gap-4"><div><div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.17em] text-amber-100/65"><span className="size-1.5 rounded-full bg-amber-200" /> Project in development</div><h1 className="mt-2 font-[family-name:var(--font-cinema)] text-3xl tracking-[-0.035em] sm:text-4xl">{projectTitle}</h1></div><TabsList variant="line" className="max-w-full overflow-x-auto text-white/60"><TabsTrigger value="story">Story</TabsTrigger><TabsTrigger value="characters">Characters</TabsTrigger><TabsTrigger value="scenes">Scenes</TabsTrigger><TabsTrigger value="shots">Shots</TabsTrigger><TabsTrigger value="keyframes">Keyframes</TabsTrigger><TabsTrigger value="videos">Videos</TabsTrigger><TabsTrigger value="timeline">Timeline</TabsTrigger></TabsList></div>

              <TabsContent value="story" className="space-y-6">
                <div className="grid gap-5 lg:grid-cols-[1.35fr_.65fr]"><div className="rounded-2xl border border-white/10 bg-white/[0.035] p-5 sm:p-6"><div className="flex items-center justify-between"><span className="text-xs font-semibold uppercase tracking-[.16em] text-white/38">Original story</span><button className="text-xs text-amber-100 hover:text-amber-50">Edit brief</button></div><p className="mt-5 max-w-2xl text-lg leading-8 text-white/88">{prompt}</p><div className="mt-7 flex flex-wrap gap-2"><Pill>Speculative drama</Pill><Pill>Desert mystery</Pill><Pill>2.5 min</Pill><Pill>2.39:1</Pill></div></div><div className="rounded-2xl border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(251,191,36,.12),transparent_48%),rgba(255,255,255,.03)] p-5 sm:p-6"><span className="text-xs font-semibold uppercase tracking-[.16em] text-white/38">Style bible</span><p className="mt-4 font-[family-name:var(--font-cinema)] text-2xl leading-tight text-amber-50">"Ancient futurism at blue hour."</p><p className="mt-3 text-sm leading-6 text-white/50">Sun-bleached geometry, cyan practical light, anamorphic flare, delicate grain.</p></div></div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.025]"><div className="flex items-center justify-between border-b border-white/10 px-5 py-4 sm:px-6"><div><h2 className="font-medium">Creative direction</h2><p className="mt-1 text-sm text-white/45">A reusable foundation for every image and clip.</p></div><Button variant="outline" className="border-white/14 bg-transparent text-white hover:bg-white/7 hover:text-white">View bible <ArrowRight className="size-3.5" /></Button></div><div className="grid divide-y divide-white/8 sm:grid-cols-3 sm:divide-x sm:divide-y-0"><Direction label="Lens language" value="35mm / 75mm, shallow focus" /><Direction label="Colour passage" value="Sandstone → electric blue" /><Direction label="Camera movement" value="Slow, purposeful drift" /></div></div>
              </TabsContent>
              <TabsContent value="characters"><div className="mb-6 flex items-end justify-between"><div><h2 className="text-xl font-medium">Character references</h2><p className="mt-1 text-sm text-white/48">Canonical identities are carried into every shot.</p></div><Button variant="outline" className="border-white/14 bg-transparent text-white hover:bg-white/7 hover:text-white"><WandSparkles className="size-4" /> Add character</Button></div><div className="grid gap-4 md:grid-cols-3">{characters.map((character) => <article key={character.name} className="overflow-hidden rounded-2xl border border-white/10 bg-white/[.03]"><div className={`relative aspect-[4/3] bg-gradient-to-br ${character.color}`}><div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/65 to-transparent" /><span className="absolute bottom-4 left-4 flex size-10 items-center justify-center rounded-full border border-white/25 bg-black/20 text-sm font-semibold text-white">{character.initials}</span></div><div className="p-4"><div className="flex items-start justify-between gap-3"><div><h3 className="font-medium">{character.name}</h3><p className="mt-1 text-sm text-white/45">{character.role}</p></div><button className="text-white/40 hover:text-white"><MoreHorizontal className="size-4" /></button></div><div className="mt-4 flex gap-2"><Button size="sm" variant="outline" className="border-white/14 bg-transparent text-white hover:bg-white/7 hover:text-white">Regenerate</Button><Button size="sm" className="bg-emerald-400/15 text-emerald-200 hover:bg-emerald-400/25">Approved <Check className="size-3.5" /></Button></div></div></article>)}</div></TabsContent>
              <TabsContent value="scenes"><div className="mb-6 flex items-end justify-between"><div><h2 className="text-xl font-medium">Scene plan</h2><p className="mt-1 text-sm text-white/48">Narrative sequences are developed before filmable shots.</p></div><Button className="bg-amber-200 text-[#17140f] hover:bg-amber-100"><WandSparkles className="size-4" /> Regenerate plan</Button></div><div className="space-y-3">{scenes.map((scene) => <article key={scene.number} className={`overflow-hidden rounded-xl border transition ${expanded === scene.number ? 'border-amber-200/30 bg-amber-200/[.045]' : 'border-white/10 bg-white/[.025]'}`}><button onClick={() => setExpanded(expanded === scene.number ? '' : scene.number)} className="flex w-full items-center gap-4 px-4 py-4 text-left sm:px-5"><span className="font-[family-name:var(--font-cinema)] text-2xl text-white/30">{scene.number}</span><span className="min-w-0 flex-1"><span className="block truncate font-medium text-white/90">{scene.title}</span><span className="mt-1 block text-xs text-white/42">{scene.shots} shots · {scene.duration}</span></span><span className={`hidden rounded-full px-2.5 py-1 text-xs sm:inline ${scene.status === 'ready' ? 'bg-emerald-400/10 text-emerald-200' : scene.status === 'active' ? 'bg-amber-200/10 text-amber-100' : 'bg-white/6 text-white/40'}`}>{scene.status === 'active' ? 'Needs review' : scene.status}</span>{expanded === scene.number ? <ChevronDown className="size-4 text-white/50" /> : <ChevronRight className="size-4 text-white/50" />}</button>{expanded === scene.number && <div className="border-t border-white/10 px-5 py-5"><p className="max-w-3xl text-sm leading-6 text-white/63">Mara enters a monumental underground avenue as the city’s dormant systems respond to her presence. Blue light rises through dust and turns the excavation into a threshold between history and a living intelligence.</p><div className="mt-5 flex flex-wrap gap-2"><Pill>Subterranean avenue</Pill><Pill>Mara Voss</Pill><Pill>Blue-hour lighting</Pill><Pill>Continuity: dust on jacket</Pill></div><div className="mt-5 flex gap-2"><Button size="sm" variant="outline" className="border-white/14 bg-transparent text-white hover:bg-white/7 hover:text-white">Edit scene</Button><Button size="sm" className="bg-amber-200 text-[#17140f] hover:bg-amber-100">Approve scene <ArrowRight className="size-3.5" /></Button></div></div>}</article>)}</div></TabsContent>
              <TabsContent value="shots"><ShotBoard /></TabsContent>
              <TabsContent value="keyframes"><ShotBoard /></TabsContent>
              <TabsContent value="videos"><ShotBoard /></TabsContent>
              <TabsContent value="timeline"><div className="rounded-2xl border border-dashed border-white/15 bg-white/[.02] p-12 text-center"><Film className="mx-auto size-7 text-amber-100/60" /><h2 className="mt-4 text-lg font-medium">Your timeline will take shape here</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-white/45">Approve the scene plan, then Hollywood will line up each completed clip in story order.</p></div></TabsContent>
            </Tabs>
          </section>

          <aside className="hidden border-l border-white/10 bg-[#0c1016]/70 p-5 xl:block"><div className="flex items-center justify-between"><div className="flex items-center gap-2 text-sm font-medium"><PanelRight className="size-4 text-amber-100" /> Inspector</div><button className="text-white/40 hover:text-white"><MoreHorizontal className="size-4" /></button></div><div className="mt-7"><label className="text-xs font-semibold uppercase tracking-[.15em] text-white/36">Pipeline status</label><div className="mt-4 space-y-4">{stages.map((stage) => <div key={stage.label} className="flex items-start gap-3"><div className="mt-0.5"><StageDot state={stage.state} /></div><div><p className={`text-sm ${stage.state === 'pending' ? 'text-white/38' : 'text-white/84'}`}>{stage.label}</p><p className="mt-0.5 text-xs text-white/37">{stage.detail}</p></div></div>)}</div></div><div className="mt-9 border-t border-white/10 pt-6"><label className="text-xs font-semibold uppercase tracking-[.15em] text-white/36">Output settings</label><div className="mt-4 space-y-4"><Select defaultValue="cinematic"><SelectTrigger className="w-full border-white/12 bg-white/[.035] text-white"><SelectValue placeholder="Visual style" /></SelectTrigger><SelectContent><SelectItem value="cinematic">Cinematic realism</SelectItem><SelectItem value="animation">Stylized animation</SelectItem><SelectItem value="documentary">Documentary</SelectItem></SelectContent></Select><Select defaultValue="239"><SelectTrigger className="w-full border-white/12 bg-white/[.035] text-white"><SelectValue placeholder="Aspect ratio" /></SelectTrigger><SelectContent><SelectItem value="239">2.39:1 widescreen</SelectItem><SelectItem value="169">16:9 landscape</SelectItem><SelectItem value="916">9:16 portrait</SelectItem></SelectContent></Select><label className="flex items-center justify-between text-sm text-white/67"><span>Director checkpoints</span><Switch checked={directorMode} onCheckedChange={setDirectorMode} /></label></div></div></aside>
        </div>
      </main>
    </TooltipProvider>
  );
}

function Brand({ compact = false }: { compact?: boolean }) {
  return <div className="flex items-center gap-2.5"><span className="flex size-8 items-center justify-center rounded-lg bg-amber-200 text-[#15130f] shadow-[0_0_24px_rgba(251,191,36,.18)]"><Clapperboard className="size-4" /></span><span className={`font-[family-name:var(--font-cinema)] text-xl tracking-[-.03em] ${compact ? 'hidden sm:inline' : ''}`}>HOLLYWOOD</span></div>;
}

function Pill({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full border border-white/10 bg-white/[.035] px-2.5 py-1 text-xs text-white/58">{children}</span>;
}

function Direction({ label, value }: { label: string; value: string }) {
  return <div className="p-5 sm:p-6"><p className="text-xs font-semibold uppercase tracking-[.15em] text-white/35">{label}</p><p className="mt-2 text-sm leading-6 text-white/73">{value}</p></div>;
}

function ShotBoard() {
  return <div><div className="mb-6 flex items-end justify-between"><div><h2 className="text-xl font-medium">Shot 02 · The city exhales</h2><p className="mt-1 text-sm text-white/48">Start, motion, and ending intention stay linked.</p></div><Button className="bg-amber-200 text-[#17140f] hover:bg-amber-100"><WandSparkles className="size-4" /> Generate video</Button></div><div className="grid gap-3 md:grid-cols-3"><FilmStill kind="start" label="Start frame" /><FilmStill kind="video" label="Clip · 06s" /><FilmStill kind="end" label="End frame" /></div><div className="mt-5 grid gap-5 rounded-2xl border border-white/10 bg-white/[.025] p-5 lg:grid-cols-[1fr_260px]"><div><p className="text-xs font-semibold uppercase tracking-[.15em] text-white/35">Generation prompt</p><p className="mt-3 text-sm leading-6 text-white/70">Mara walks through a monumental underground avenue as cobalt light progressively climbs its carved walls. The camera tracks beside her from a medium-wide frame, gradually revealing the city’s impossible scale. Dust rolls around her boots; her expression moves from wary concentration to awe. Anamorphic cinematic realism, rich sandstone and blue contrasts, subtle film grain.</p></div><div className="border-t border-white/10 pt-5 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0"><p className="text-xs font-semibold uppercase tracking-[.15em] text-white/35">Direction</p><dl className="mt-3 space-y-3 text-sm"><div className="flex justify-between gap-3"><dt className="text-white/45">Duration</dt><dd>6 seconds</dd></div><div className="flex justify-between gap-3"><dt className="text-white/45">Camera</dt><dd>Side track</dd></div><div className="flex justify-between gap-3"><dt className="text-white/45">Continuity</dt><dd className="text-emerald-200">Balanced</dd></div></dl><Button variant="outline" className="mt-5 w-full border-white/14 bg-transparent text-white hover:bg-white/7 hover:text-white">Edit shot</Button></div></div></div>;
}
