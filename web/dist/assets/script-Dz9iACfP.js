(function(){const n=document.createElement("link").relList;if(n&&n.supports&&n.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))i(o);new MutationObserver(o=>{for(const a of o)if(a.type==="childList")for(const u of a.addedNodes)u.tagName==="LINK"&&u.rel==="modulepreload"&&i(u)}).observe(document,{childList:!0,subtree:!0});function e(o){const a={};return o.integrity&&(a.integrity=o.integrity),o.referrerPolicy&&(a.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?a.credentials="include":o.crossOrigin==="anonymous"?a.credentials="omit":a.credentials="same-origin",a}function i(o){if(o.ep)return;o.ep=!0;const a=e(o);fetch(o.href,a)}})();document.addEventListener("DOMContentLoaded",()=>{q(),O(),N(),$(),j(),F(),z(),W(),U(),X(),K(),Y(),Q(),J(),Z(),ee(),ie(),se(),ae()});function q(){const t=document.getElementById("hero-canvas");if(!t)return;const n=t.getContext("2d",{alpha:!0});let e=t.width=window.innerWidth,i=t.height=window.innerHeight,o;window.addEventListener("resize",()=>{clearTimeout(o),o=setTimeout(()=>{e=t.width=window.innerWidth,i=t.height=window.innerHeight},150)},{passive:!0});const a=[],u=Math.min(Math.floor(e/30),45);for(let p=0;p<u;p++)a.push({x:Math.random()*e,y:Math.random()*i,radius:Math.random()*2+1,color:Math.random()>.5?"rgba(99, 102, 241, ":"rgba(236, 72, 153, ",alpha:Math.random()*.5+.2,vx:(Math.random()-.5)*.35,vy:(Math.random()-.5)*.35});let m;function h(){n.clearRect(0,0,e,i);for(let p=0;p<a.length;p++){const c=a[p];c.x+=c.vx,c.y+=c.vy,c.x<0&&(c.x=e),c.x>e&&(c.x=0),c.y<0&&(c.y=i),c.y>i&&(c.y=0),n.beginPath(),n.arc(c.x,c.y,c.radius,0,Math.PI*2),n.fillStyle=c.color+c.alpha+")",n.fill();for(let f=p+1;f<a.length;f++){const v=a[f],d=c.x-v.x,s=c.y-v.y,r=d*d+s*s;if(r<14400){const l=Math.sqrt(r);n.beginPath(),n.moveTo(c.x,c.y),n.lineTo(v.x,v.y),n.strokeStyle=`rgba(139, 92, 246, ${.12*(1-l/120)})`,n.lineWidth=.5,n.stroke()}}}m=requestAnimationFrame(h)}document.addEventListener("visibilitychange",()=>{document.hidden?cancelAnimationFrame(m):h()}),h()}function O(){const t=document.getElementById("mobile-menu-btn"),n=document.getElementById("mobile-menu");!t||!n||(t.addEventListener("click",()=>{n.classList.toggle("hidden");const e=t.querySelector("i");e&&(n.classList.contains("hidden")?e.className="fas fa-bars text-2xl":e.className="fas fa-times text-2xl text-pink-400")}),n.querySelectorAll("a").forEach(e=>{e.addEventListener("click",()=>{n.classList.add("hidden");const i=t.querySelector("i");i&&(i.className="fas fa-bars text-2xl")})}))}function N(){const t=document.querySelectorAll(".nav-dropdown");t.forEach(n=>{const e=n.querySelector("button");e&&e.addEventListener("click",i=>{i.stopPropagation(),n.classList.toggle("is-open")})}),document.addEventListener("click",n=>{t.forEach(e=>{e.contains(n.target)||e.classList.remove("is-open")})})}function $(){const t=document.querySelectorAll(".reveal-on-scroll");if(!t.length)return;const n=new IntersectionObserver((e,i)=>{e.forEach(o=>{o.isIntersecting&&(o.target.classList.add("is-visible"),i.unobserve(o.target))})},{threshold:.12,rootMargin:"0px 0px -40px 0px"});t.forEach(e=>n.observe(e))}function j(){const t=document.querySelectorAll("[data-counter]");if(!t.length)return;const n=new IntersectionObserver((e,i)=>{e.forEach(o=>{if(o.isIntersecting){let f=function(v){const d=v-c,s=Math.min(d/p,1),r=Math.floor((1-Math.pow(1-s,3))*m);u.textContent=r+h,s<1?requestAnimationFrame(f):u.textContent=m+h};var a=f;const u=o.target,m=parseInt(u.getAttribute("data-counter"),10),h=u.getAttribute("data-suffix")||"",p=1500,c=performance.now();requestAnimationFrame(f),i.unobserve(u)}})},{threshold:.5});t.forEach(e=>n.observe(e))}function F(){const t=document.querySelectorAll(".filter-btn[data-filter]"),n=document.querySelectorAll(".repo-card[data-category]");!t.length||!n.length||t.forEach(e=>{e.addEventListener("click",()=>{t.forEach(o=>o.classList.remove("active")),e.classList.add("active");const i=e.getAttribute("data-filter");n.forEach(o=>{const a=o.getAttribute("data-category");i==="all"||a===i?(o.style.display="flex",setTimeout(()=>{o.style.opacity="1",o.style.transform="translateY(0)"},50)):(o.style.opacity="0",o.style.transform="translateY(20px)",setTimeout(()=>{o.style.display="none"},250))})})})}function z(){const t=document.getElementById("calc-team"),n=document.getElementById("calc-hours"),e=document.getElementById("calc-rate");if(!t||!n||!e)return;const i=document.getElementById("calc-team-val"),o=document.getElementById("calc-hours-val"),a=document.getElementById("calc-rate-val"),u=document.getElementById("res-hours-saved"),m=document.getElementById("res-money-saved");function h(){const p=parseInt(t.value,10),c=parseInt(n.value,10),f=parseInt(e.value,10);i.textContent=p,o.textContent=`${c} hrs/wk`,a.textContent=`$${f}/hr`;const v=Math.round(p*c*52*.75),d=Math.round(v*f);u.textContent=`${v.toLocaleString()} hrs`,m.textContent=`$${d.toLocaleString()}`}t.addEventListener("input",h,{passive:!0}),n.addEventListener("input",h,{passive:!0}),e.addEventListener("input",h,{passive:!0}),h()}const V={"tutorbot-agents":{title:"DeepTutor Platform (TutorBot Agents)",category:"AI Agents & Lifelong Learning Copilots",description:"Agent-native personalized tutoring ecosystem developed by HKUDS & Xennials. Includes 8 synchronized learning surfaces, 3-layer persistent cognitive memory, and multi-turn Socratic reasoning.",tech:["Next.js","React","TutorBot Agent Swarm","FastAPI","RAG Engine","Vector DB"],url:"deeptutor.html",isApp:!0},"xennials-agent":{title:"Xennials AI Autonomous Suite",category:"Autonomous Multi-Agent Enterprise Suite",description:"Personal AI agent runtime & Enterprise Suite integration with byte-stable prompt caching, multi-platform messaging gateway (Telegram, Discord, WeChat, Slack), 1,069+ skills, interactive video ads, and full CRM automation.",tech:["FastAPI","React 19","Vite","Xennials Agent Core","Enterprise CRM","NVIDIA NIM"],url:"https://xennials-agent.netlify.app/",isApp:!0},"ui-components":{title:"21st - UI Components Design System",category:"Frontend Engineering",description:"Component marketplace for design engineers built on shadcn/ui and TailwindCSS. Offers ready-to-use micro-animations, glassmorphism cards, dynamic charts, and interactive hooks.",tech:["React","TailwindCSS","Framer Motion","TypeScript"],url:"https://github.com/teefisher2k20/21st"},"adk-python":{title:"ADK Python (AI Development Kit)",category:"Agentic AI Framework",description:"Code-first Python toolkit designed to build, evaluate, and orchestrate complex multi-agent LLM systems with custom memory management and tool routing.",tech:["Python 3.11","LangChain","FastAPI","Pydantic","AsyncIO"],url:"https://github.com/teefisher2k20/adk-python"},"agent-e":{title:"Agent-E Web Automation Engine",category:"Headless Browser Automation",description:"Agentic automation engine built for autonomous web navigation, DOM parsing, structured data extraction, and automated form execution.",tech:["Python","Playwright","Puppeteer","AI Vision"],url:"https://github.com/teefisher2k20/agent-e"},"vscode-tools":{title:"VS Code Developer Suite",category:"Developer Tooling",description:"Custom open-source extension pack enhancing developer velocity with AI code completion, quick syntax snippets, and automated test triggers.",tech:["TypeScript","VS Code API","JSON Schema"],url:"https://github.com/teefisher2k20/vscode"}};function W(){const t=document.getElementById("project-modal"),n=document.getElementById("modal-close-btn");if(!t)return;document.querySelectorAll("[data-project-key]").forEach(i=>{i.addEventListener("click",o=>{o.preventDefault();const a=i.getAttribute("data-project-key"),u=V[a];if(!u)return;document.getElementById("modal-title").textContent=u.title,document.getElementById("modal-category").textContent=u.category,document.getElementById("modal-description").textContent=u.description;const m=document.getElementById("modal-link");m.href=u.url,u.isApp?(m.innerHTML='Explore DeepTutor Platform <i class="fas fa-arrow-right text-xs ml-1"></i>',m.className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-semibold rounded-xl text-sm transition-all shadow-lg inline-flex items-center gap-2 font-mono"):(m.innerHTML='Open on GitHub <i class="fas fa-external-link-alt text-xs ml-1"></i>',m.className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-sm transition-colors inline-flex items-center gap-2");const h=document.getElementById("modal-tech");h.replaceChildren(),u.tech.forEach(p=>{const c=document.createElement("span");c.className="px-3 py-1 bg-slate-800 border border-slate-700 text-indigo-300 text-xs rounded-lg font-mono",c.textContent=p,h.appendChild(c)}),t.classList.add("active"),document.body.style.overflow="hidden"})});function e(){t.classList.remove("active"),document.body.style.overflow=""}n&&n.addEventListener("click",e),t.addEventListener("click",i=>{i.target===t&&e()}),document.addEventListener("keydown",i=>{i.key==="Escape"&&t.classList.contains("active")&&e()})}function U(){const t=document.querySelectorAll(".theme-option"),n=localStorage.getItem("xennials_theme")||"default";n!=="default"&&document.body.setAttribute("data-theme",n),t.forEach(e=>{e.addEventListener("click",()=>{const i=e.getAttribute("data-theme-name");i==="default"?(document.body.removeAttribute("data-theme"),localStorage.setItem("xennials_theme","default")):(document.body.setAttribute("data-theme",i),localStorage.setItem("xennials_theme",i)),S(`Theme updated to ${i}`)})})}function S(t){let n=document.getElementById("toast");n||(n=document.createElement("div"),n.id="toast",n.innerHTML='<i class="fas fa-check-circle text-emerald-400 text-lg"></i> <span id="toast-msg"></span>',document.body.appendChild(n));const e=document.getElementById("toast-msg")||n.querySelector("span");e&&(e.textContent=t),n.classList.add("show"),setTimeout(()=>{n.classList.remove("show")},2800)}function Y(){document.querySelectorAll(".copy-btn, .copy-badge").forEach(t=>{t.addEventListener("click",n=>{var i;n.preventDefault();const e=t.getAttribute("data-copy")||((i=t.parentElement.querySelector("code"))==null?void 0:i.textContent);e&&navigator.clipboard.writeText(e).then(()=>{S("Copied to clipboard!")}).catch(()=>{S("Failed to copy")})})})}function X(){const t=document.getElementById("contact-form");t&&t.addEventListener("submit",n=>{n.preventDefault();const e=t.querySelector('button[type="submit"]'),i=e.innerHTML;e.innerHTML='<i class="fas fa-spinner fa-spin mr-2"></i> Transmitting...',e.disabled=!0,setTimeout(()=>{e.innerHTML='<i class="fas fa-check mr-2"></i> Message Sent!',e.classList.replace("from-indigo-600","from-emerald-600"),e.classList.replace("to-pink-600","to-teal-600"),S("Thank you! Your message has been received."),t.reset(),setTimeout(()=>{e.innerHTML=i,e.disabled=!1,e.classList.replace("from-emerald-600","from-indigo-600"),e.classList.replace("to-teal-600","to-pink-600")},3e3)},1200)})}function K(){const t=document.getElementById("back-to-top");t&&(window.addEventListener("scroll",()=>{window.scrollY>400?t.classList.add("visible"):t.classList.remove("visible")},{passive:!0}),t.addEventListener("click",()=>{window.scrollTo({top:0,behavior:"smooth"})}))}function Q(){const t=document.getElementById("sim-input-form"),n=document.getElementById("sim-user-input"),e=document.getElementById("sim-messages"),i=document.getElementById("toggle-reasoning-btn"),o=document.getElementById("sim-reasoning"),a=document.querySelectorAll(".subject-btn"),u=document.querySelectorAll(".persona-btn"),m=document.querySelectorAll(".preset-pill");if(!t||!e)return;const h={attention:{query:"How does Multi-Head Self-Attention compute queries, keys, and values?",topic:"[AI Systems]",steps:['1. [RAG Engine] Retrieved "Attention Is All You Need" (Vaswani et al.) Sec 3.2.',"2. [Cognitive Model] Learner understands matrix multiplication; needs visual breakdown of scaled dot-product.","3. [Socratic Goal] Explain linear projections first, formulate question on why dimension d_k scaling prevents vanishing gradients."],aiHtml:`
                <p>In Self-Attention, an input sequence is projected into three distinct representations through learned weight matrices:</p>
                <div class="bg-slate-950 p-3 rounded-lg font-mono text-xs text-indigo-300 border border-slate-800 my-2">
                    Q = X · W_Q &emsp;|&emsp; K = X · W_K &emsp;|&emsp; V = X · W_V
                </div>
                <p>We then compute the scaled dot-product attention formula:</p>
                <div class="latex-math text-center py-2 text-sm my-2">
                    Attention(Q, K, V) = softmax((Q · Kᵀ) / √d_k) · V
                </div>
                <p class="text-sm text-gray-300 mt-2">
                    <strong>Socratic Question for You:</strong> Why do we divide by <span class="latex-math">√d_k</span> inside the softmax rather than directly passing <span class="latex-math">Q · Kᵀ</span>? What happens to the gradients when <span class="latex-math">d_k</span> grows very large?
                </p>
            `},gradient:{query:"Derive the Gradient Descent weight update rule for Mean Squared Error loss.",topic:"[Mathematics]",steps:["1. [RAG Engine] Retrieved Optimization & Linear Models chapter (Bishop PRML).","2. [Cognitive Model] Learner knows partial derivatives; wants step-by-step vector calculus proof.","3. [Socratic Goal] Show MSE derivative with respect to weights and highlight the learning rate step."],aiHtml:`
                <p>Given the MSE loss function <span class="latex-math">L(w) = (1/2N) ∑ (y_i - wᵀx_i)²</span>, we calculate the gradient:</p>
                <div class="bg-slate-950 p-3 rounded-lg font-mono text-xs text-pink-300 border border-slate-800 my-2">
                    ∇_w L(w) = - (1/N) ∑ (y_i - wᵀx_i) x_i
                </div>
                <p>The parameter update with learning rate <span class="latex-math">η</span> becomes:</p>
                <div class="latex-math text-center py-2 text-sm my-2">
                    w_{t+1} = w_t - η · ∇_w L(w_t)
                </div>
                <p class="text-sm text-gray-300 mt-2">
                    <strong>Socratic Question for You:</strong> If we set the learning rate <span class="latex-math">η</span> too large, what geometric behavior will the parameter trajectory exhibit across the loss contour?
                </p>
            `},redblack:{query:"Explain Red-Black Tree balancing invariants and rotation rules during insertion.",topic:"[Computer Science]",steps:["1. [RAG Engine] Retrieved Cormen CLRS Chapter 13: Red-Black Trees.","2. [Cognitive Model] Learner understands BSTs; verifying color flips vs left/right rotations.","3. [Socratic Goal] Outline the 5 fundamental properties and quiz on uncle node colors."],aiHtml:`
                <p>Red-Black Trees maintain <span class="latex-math">O(log n)</span> search, insertion, and deletion by enforcing 5 critical invariants:</p>
                <ul class="list-disc pl-5 space-y-1 text-xs text-gray-300 my-2">
                    <li>1. Every node is either Red or Black.</li>
                    <li>2. The root is always Black.</li>
                    <li>3. All NIL leaves are Black.</li>
                    <li>4. If a node is Red, both its children must be Black (no adjacent red nodes).</li>
                    <li>5. For every node, all paths to descendant leaves contain the exact same number of black nodes.</li>
                </ul>
                <p class="text-sm text-gray-300 mt-2">
                    <strong>Socratic Question for You:</strong> When inserting a new node <span class="font-mono text-pink-400">Z</span> and its uncle is <strong>Red</strong>, do we need tree rotations or only color flips?
                </p>
            `},schrodinger:{query:"How is the Time-Dependent Schrödinger Equation formulated for a 1D potential well?",topic:"[Physics]",steps:["1. [RAG Engine] Retrieved Griffiths Quantum Mechanics Chapter 2.","2. [Cognitive Model] Learner is exploring Hamiltonian operators and wavefunctions.","3. [Socratic Goal] Present the general PDE and examine boundary conditions at the infinite barriers."],aiHtml:`
                <p>In one dimension, the time-dependent Schrödinger equation is given by:</p>
                <div class="latex-math text-center py-2 text-sm my-2">
                    iℏ (∂Ψ(x,t) / ∂t) = [ - (ℏ² / 2m) (∂² / ∂x²) + V(x) ] Ψ(x,t)
                </div>
                <p>For an infinite square well of width <span class="latex-math">L</span>, the spatial wavefunctions quantize to:</p>
                <div class="bg-slate-950 p-3 rounded-lg font-mono text-xs text-cyan-300 border border-slate-800 my-2">
                    ψ_n(x) = √(2/L) · sin(nπx / L), &emsp; n = 1, 2, 3...
                </div>
                <p class="text-sm text-gray-300 mt-2">
                    <strong>Socratic Question for You:</strong> Why is the ground state energy <span class="latex-math">E_1 > 0</span> rather than 0? How does Heisenberg's Uncertainty Principle mandate this?
                </p>
            `}};function p(s){const r=h[s];if(!r)return;const l=document.getElementById("sim-topic-tag");l&&(l.textContent=r.topic);const y=document.getElementById("sim-user-query");if(y&&(y.textContent=r.query),o){const x=o.querySelector("ul");x&&(x.replaceChildren(),r.steps.forEach(E=>{const L=document.createElement("li");L.textContent=E,x.appendChild(L)}))}const b=document.getElementById("sim-ai-response");b&&(b.innerHTML=r.aiHtml);const C=document.getElementById("sim-retention-score"),T=document.getElementById("sim-progress-bar");if(C&&T){const x=(92+Math.random()*6).toFixed(1);C.textContent=`${x}%`,T.style.width=`${x}%`}}i&&o&&i.addEventListener("click",()=>{o.classList.toggle("hidden");const s=o.classList.contains("hidden");i.innerHTML=s?'<i class="fas fa-eye mr-1 text-indigo-400"></i> Show Reasoning':'<i class="fas fa-stream mr-1 text-indigo-400"></i> Chain-of-Thought'}),a.forEach(s=>{s.addEventListener("click",()=>{a.forEach(y=>{y.classList.remove("active","border-indigo-500/50","bg-indigo-950/40","text-white"),y.classList.add("border-slate-800","bg-slate-950/40","text-gray-300")}),s.classList.add("active","border-indigo-500/50","bg-indigo-950/40","text-white"),s.classList.remove("border-slate-800","bg-slate-950/40","text-gray-300");const r=s.getAttribute("data-subject"),l={ai:"attention",math:"gradient",cs:"redblack",physics:"schrodinger"};l[r]&&p(l[r])})}),u.forEach(s=>{s.addEventListener("click",()=>{u.forEach(l=>{l.classList.remove("active","border-pink-500/50","bg-pink-950/30","text-white"),l.classList.add("border-slate-800","bg-slate-950/40","text-gray-300")}),s.classList.add("active","border-pink-500/50","bg-pink-950/30","text-white"),s.classList.remove("border-slate-800","bg-slate-950/40","text-gray-300");const r=document.getElementById("sim-agent-name");if(r){const l=s.getAttribute("data-persona"),y={socratic:"DeepTutor • Socratic Mentor",architect:"DeepTutor • Code Architect",scientist:"DeepTutor • First Principles",crammer:"DeepTutor • Exam Drill"};r.textContent=y[l]||"DeepTutor • Agent Core"}})}),m.forEach(s=>{s.addEventListener("click",()=>{const r=s.getAttribute("data-prompt");p(r)})});const c=["Explain how Scaled Dot-Product Attention maintains gradient stability as key dimension d_k increases.","Derive the Backpropagation equations for a 2-layer MLP with Cross-Entropy Loss from first principles.","Prove that any comparison-based sorting algorithm has a lower bound of Ω(n log n) comparisons.","How do Raft consensus leader election and log replication guarantees prevent split-brain partitions?","Explain the physics of quantum entanglement and Bell's theorem violation in EPR paradox experiments.","Analyze why transformer KV-cache memory usage scales linearly with sequence length O(N) and batch size.","Derive the Euler-Lagrange equations from the Principle of Stationary Action in classical mechanics.","Explain the formal proof of Gödel's First Incompleteness Theorem using Gödel numbering and self-reference.","How does TCP BBR congestion control estimate bottleneck bandwidth and round-trip propagation time without packet loss?","Explain Fourier Transform duality: why sharp localization in the time domain creates broad spread in the frequency domain."],f=document.getElementById("random-sim-prompt-btn"),v=document.getElementById("random-sim-icon-btn"),d=s=>{const r=c[Math.floor(Math.random()*c.length)];n&&(n.value=r,n.classList.remove("prompt-flash-highlight"),n.offsetWidth,n.classList.add("prompt-flash-highlight"),n.focus()),s&&(s.classList.add("rolling"),setTimeout(()=>s.classList.remove("rolling"),500))};f&&f.addEventListener("click",()=>d(f)),v&&v.addEventListener("click",()=>d(v)),t.addEventListener("submit",s=>{s.preventDefault();const r=n.value.trim();if(!r)return;const l=document.createElement("div");l.className="agent-chat-bubble user max-w-[85%]",l.innerHTML=`<p>${r}</p>`,e.appendChild(l),n.value="";const y=document.createElement("div");y.className="agent-chat-bubble ai max-w-[90%] space-y-2",y.innerHTML=`
            <div class="flex items-center gap-2 text-indigo-400 text-xs font-mono mb-1">
                <i class="fas fa-spinner fa-spin"></i> DeepTutor Socratic Synthesis...
            </div>
            <p>Analyzing foundational concepts in: <em>"${r}"</em></p>
        `,e.appendChild(y),e.scrollTop=e.scrollHeight,setTimeout(()=>{y.innerHTML=`
                <p>To master <strong>${r}</strong>, let's break this down into first principles:</p>
                <div class="bg-slate-950 p-3 rounded-lg font-mono text-xs text-indigo-300 border border-slate-800 my-2">
                    Core Rule: Deconstruct the problem into elementary axioms & verified invariants.
                </div>
                <p class="text-sm text-gray-300">
                    <strong>Socratic Prompt:</strong> How does this concept connect to your existing knowledge base in calculus and algorithms? Try defining the input-output boundary condition first.
                </p>
            `,e.scrollTop=e.scrollHeight},900)})}function J(){const t=document.getElementById("generate-btn"),n=document.getElementById("prompt-input"),e=document.getElementById("canvas-preview"),i=document.querySelectorAll(".style-tag");!t||!e||(i.forEach(o=>{o.addEventListener("click",()=>{i.forEach(a=>{a.classList.remove("bg-indigo-950","border-indigo-500/50","text-indigo-300"),a.classList.add("bg-slate-800","border-slate-700","text-gray-400")}),o.classList.add("bg-indigo-950","border-indigo-500/50","text-indigo-300"),o.classList.remove("bg-slate-800","border-slate-700","text-gray-400")})}),t.addEventListener("click",()=>{const o=n?n.value.trim():"",a=t.innerHTML;t.innerHTML='<i class="fas fa-spinner fa-spin mr-2"></i> Synthesizing Latents...',t.disabled=!0,e.innerHTML=`
            <div class="flex flex-col items-center justify-center space-y-3">
                <div class="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
                <p class="text-xs text-indigo-300 font-mono">Sampling Diffusion Steps [28/28]...</p>
            </div>
        `,setTimeout(()=>{e.innerHTML=`
                <div class="w-full h-full flex flex-col items-center justify-center relative p-6">
                    <div class="w-24 h-24 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center text-white text-4xl shadow-2xl mb-4 animate-float">
                        <i class="fas fa-cube"></i>
                    </div>
                    <h4 class="font-space font-bold text-white text-lg">Visual Synthesis Generated</h4>
                    <p class="text-xs text-indigo-300 font-mono mt-1 max-w-md">${o||"Autonomous AI Robotic Architecture in Cybernetic Stacks"}</p>
                    <div class="mt-4 flex gap-2">
                        <button class="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs font-mono text-gray-300 hover:text-white" onclick="showToast('High-Res canvas downloaded!')">
                            <i class="fas fa-download mr-1"></i> Export HD
                        </button>
                    </div>
                </div>
            `,t.innerHTML=a,t.disabled=!1,S("Visual synthesized successfully!")},1400)}))}function Z(){const t=document.getElementById("blog-search"),n=document.querySelectorAll(".filter-btn[data-category]"),e=document.querySelectorAll("[data-article-category]");if(!e.length)return;function i(){const o=t?t.value.toLowerCase().trim():"",a=document.querySelector(".filter-btn[data-category].active"),u=a?a.getAttribute("data-category"):"all";e.forEach(m=>{const h=m.getAttribute("data-article-category"),p=m.textContent.toLowerCase(),c=u==="all"||h===u,f=!o||p.includes(o);c&&f?m.style.display="":m.style.display="none"})}t&&t.addEventListener("input",i,{passive:!0}),n.forEach(o=>{o.addEventListener("click",()=>{n.forEach(a=>a.classList.remove("active")),o.classList.add("active"),i()})})}function ee(){te(),ne(),oe()}function te(){const t=document.querySelectorAll(".workflow-tab-btn"),n=document.querySelectorAll(".workflow-tab-content");t.length&&t.forEach(e=>{e.addEventListener("click",()=>{const i=e.getAttribute("data-wf-tab");t.forEach(o=>o.classList.remove("active")),e.classList.add("active"),n.forEach(o=>{o.id===`wf-panel-${i}`?o.classList.remove("hidden"):o.classList.add("hidden")})})})}function ne(){const t=document.querySelectorAll(".pipeline-node"),n=document.getElementById("inspector-step-badge"),e=document.getElementById("inspector-step-title"),i=document.getElementById("inspector-step-cost"),o=document.getElementById("inspector-config-code"),a=document.getElementById("inspector-payload-code"),u=document.getElementById("run-pipeline-sim-btn"),m=document.getElementById("sim-pipeline-keyword"),h=document.getElementById("pipeline-status-text"),p=document.getElementById("pipeline-live-logs");if(!t.length)return;const c={1:{badge:"STEP 1",title:"Trigger: Google Sheets Watch Changes",cost:"Cost: $0.00 (Native Trigger)",config:`{
  "app": "Google Sheets",
  "action": "Watch Changes",
  "worksheet": "Video Queue",
  "triggerColumn": "Status = 'Pending'",
  "filter": "Keyword is not empty"
}`,payload:`// Payload emitted to downstream pipeline:
{
  "job_id": "vid_89412",
  "keyword": "how to build an automated AI business",
  "client_id": "client_acme_01",
  "tone": "casual_engaging",
  "target_duration_sec": 60
}`},2:{badge:"STEP 2",title:"Research Agent: Perplexity API / GPT-4o RAG",cost:"Cost: ~$0.02 (250 tokens)",config:`{
  "endpoint": "https://api.perplexity.ai/chat/completions",
  "model": "sonar-medium-online",
  "max_tokens": 500,
  "cache_strategy": "24h_redis_kv"
}`,payload:`// Research Output Data:
{
  "facts": [
    "Solo entrepreneurs use agent swarms to scale 10x output.",
    "Make.com + LangGraph reduces delivery time from 4h to 15m.",
    "Average API operational cost is under $0.50 per final video."
  ],
  "sources": ["https://techcrunch.com/ai-agents", "https://arxiv.org/abs/2401"]
}`},3:{badge:"STEP 3",title:"Script Synthesis: Claude 3.7 / GPT-4o",cost:"Cost: ~$0.04 (550 words / 480 tokens)",config:`{
  "model": "claude-3-7-sonnet-20250219",
  "system_prompt_id": "sys_hook_retention_v3",
  "temperature": 0.65,
  "rules": ["Hook in first 3s", "Casual tone", "CTA at end"]
}`,payload:`// Generated Script:
{
  "hook": "What if a one-person business could outproduce a 10-person media team?",
  "body": "Here is the exact 3-step agent blueprint: 1. Automated lead capture, 2. Multi-agent video assembly, 3. Zero-touch CRM delivery...",
  "duration_sec": 58
}`},4:{badge:"STEP 4",title:"Voice Synthesis: ElevenLabs Turbo v2",cost:"Cost: ~$0.15 (Turbo Model, 50% savings)",config:`{
  "url": "https://api.elevenlabs.io/v1/text-to-speech/voice_adam_turbo",
  "model_id": "eleven_turbo_v2",
  "stability": 0.5,
  "similarity_boost": 0.75
}`,payload:`// Audio Output Metadata:
{
  "audio_format": "audio/mp3",
  "duration_sec": 58.4,
  "sample_rate": 44100,
  "file_url": "https://cdn.xennials.tech/audio/voice_89412.mp3"
}`},5:{badge:"STEP 5",title:"Video Compositor: JSON2Video / Pictory API",cost:"Cost: ~$0.25 (1080p Cloud Render)",config:`{
  "resolution": "1080x1920",
  "fps": 30,
  "scenes": 7,
  "captions": "auto_animated_subtitles",
  "audio_track": "voice_89412.mp3"
}`,payload:`// Rendered Video Asset:
{
  "render_id": "rnd_44901",
  "status": "COMPLETED",
  "video_url": "https://cdn.xennials.tech/rendered/vid_89412_final.mp4",
  "filesize_mb": 24.8
}`},6:{badge:"STEP 6",title:"Auto Delivery & CRM: Drive, Notion, Stripe",cost:"Cost: $0.00 (Webhook Automation)",config:`{
  "route_a": "Google Drive: /Client_Acme/March_2026/",
  "route_b": "Notion Database: Update Status to Completed",
  "route_c": "Gmail: Auto-notify client with download link"
}`,payload:`// Delivery Confirmation:
{
  "notion_item_updated": true,
  "drive_file_id": "1xZ9...kM8",
  "client_email_sent": "client@acmestudios.com",
  "time_elapsed_total": "14m 32s"
}`}};t.forEach(f=>{f.addEventListener("click",()=>{const v=f.getAttribute("data-step-id");t.forEach(s=>s.classList.remove("active")),f.classList.add("active");const d=c[v];d&&(n&&(n.textContent=d.badge),e&&(e.textContent=d.title),i&&(i.textContent=d.cost),o&&(o.textContent=d.config),a&&(a.textContent=d.payload))})}),u&&u.addEventListener("click",()=>{const f=m?m.value.trim():"how to build an automated AI business";if(!f)return;u.disabled=!0,u.innerHTML='<i class="fas fa-spinner fa-spin"></i> <span>Executing Swarm...</span>',p&&(p.classList.remove("hidden"),p.innerHTML=`<div class="text-indigo-400">[00:00] 🚀 Initializing Autonomous Agent Swarm for: "${f}"...</div>`),h&&(h.innerHTML='Status: <span class="text-pink-400 font-bold animate-pulse">Running Swarm...</span>');const v=[{delay:800,step:1,log:`[00:02] [Make.com] Row fetched from Google Sheet. Trigger verified for keyword: "${f}".`},{delay:2e3,step:2,log:"[00:05] [Perplexity Agent] 5 research facts & citations extracted (0.8s latency, 240 tokens)."},{delay:3400,step:3,log:"[00:09] [Claude 3.7 Sonnet] High-retention 58-second script synthesized with 3-second hook."},{delay:4800,step:4,log:"[00:12] [ElevenLabs Turbo v2] Generated voiceover MP3 (Cost: $0.15, -14 LUFS normalized)."},{delay:6400,step:5,log:"[00:15] [JSON2Video Engine] Matched 7 dynamic stock scenes & rendered 1080p MP4 master."},{delay:7800,step:6,log:"[00:18] [Delivery Router] Video saved to Google Drive /Client_Acme/, Notion status updated to Completed ✅."}],d=document.getElementById("pipeline-nodes-container");d&&d.classList.add("sim-running"),v.forEach(s=>{setTimeout(()=>{t.forEach(l=>l.classList.remove("running-step"));const r=document.querySelector(`.pipeline-node[data-step-id="${s.step}"]`);if(r&&(r.classList.add("running-step"),r.click()),p){const l=document.createElement("div");l.className="text-gray-300",l.innerHTML=`<span class="text-emerald-400">✓</span> ${s.log}`,p.appendChild(l),p.scrollTop=p.scrollHeight}},s.delay)}),setTimeout(()=>{d&&d.classList.remove("sim-running"),t.forEach(s=>s.classList.remove("running-step")),u.disabled=!1,u.innerHTML='<i class="fas fa-check-circle"></i> <span>Simulation Complete (Run Again)</span>',h&&(h.innerHTML='Status: <span class="text-emerald-400 font-bold">Delivered (100% Zero-Touch)</span>'),S("Pipeline execution simulation complete!")},8500)})}function oe(){const t=document.getElementById("cost-calc-jobs"),n=document.getElementById("cost-calc-jobs-val"),e=document.getElementById("cost-opt-cache"),i=document.getElementById("cost-opt-routing"),o=document.getElementById("cost-unopt-total"),a=document.getElementById("cost-opt-total"),u=document.getElementById("cost-savings-monthly");if(!t)return;function m(){const h=parseInt(t.value,10);n&&(n.textContent=`${h} videos`);const p=2.1;let c=2.1;i&&i.checked&&(c-=.9),e&&e.checked&&(c-=.74),c=Math.max(.46,c);const f=h*p,v=h*c,d=f-v;o&&(o.textContent=`$${f.toFixed(2)}/mo`),a&&(a.textContent=`$${v.toFixed(2)}/mo`),u&&(u.textContent=`$${d.toFixed(2)} / month`)}t.addEventListener("input",m),e&&e.addEventListener("change",m),i&&i.addEventListener("change",m),m()}function ie(){if(!document.getElementById("universal-hover-annotation-card")){const g=document.createElement("div");g.id="universal-hover-annotation-card",g.innerHTML=`
            <div class="flex items-center justify-between mb-2">
                <span class="annotation-step-badge" id="hover-card-step">FEATURE GUIDE</span>
                <span class="text-[10px] text-gray-500 font-mono">XENNIALS TOUR</span>
            </div>
            <h4 class="font-bold text-white text-sm mb-1 font-space" id="hover-card-title">Interactive Element</h4>
            <p class="text-xs text-gray-300 leading-relaxed mb-2" id="hover-card-desc">Description will appear here...</p>
            <div class="text-[11px] text-indigo-300 font-mono font-semibold" id="hover-card-action">👉 Click to interact</div>
        `,document.body.appendChild(g)}if(!document.getElementById("floating-tour-hud")){const g=document.createElement("div");g.id="floating-tour-hud",g.className="floating-guide-hud",g.innerHTML=`
            <button id="guide-mode-toggle" class="hud-btn hud-toggle-btn active" title="Toggle Hover Annotations & Guide Highlights">
                <i class="fas fa-lightbulb text-amber-400"></i>
                <span>Guide: <strong class="text-white">ON</strong></span>
            </button>
            <button id="start-tour-btn" class="hud-btn hud-start-tour-btn" title="Start Step-by-Step Interactive Walkthrough">
                <i class="fas fa-route"></i>
                <span>Interactive Tour</span>
            </button>
        `,document.body.appendChild(g)}if(!document.getElementById("tour-spotlight-modal")){const g=document.createElement("div");g.id="tour-spotlight-modal",g.innerHTML=`
            <div class="tour-modal-card">
                <div class="flex items-center justify-between mb-3">
                    <span class="annotation-step-badge" id="tour-modal-step">STEP 1 OF 8</span>
                    <button id="tour-modal-close" class="text-gray-400 hover:text-white text-lg focus:outline-none">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <h3 class="text-xl font-bold font-space text-white mb-2" id="tour-modal-title">Getting Started</h3>
                <p class="text-gray-300 text-sm leading-relaxed mb-5" id="tour-modal-desc">
                    Step-by-step explanation for where everything is placed...
                </p>
                <div class="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-indigo-300 font-mono mb-6" id="tour-modal-tip">
                    💡 Pro-Tip: Click anywhere on the highlighted area to test it live.
                </div>
                <div class="flex items-center justify-between pt-3 border-t border-slate-800">
                    <button id="tour-modal-prev" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-gray-300 text-xs font-semibold rounded-lg transition-colors">
                        <i class="fas fa-chevron-left mr-1"></i> Previous
                    </button>
                    <div class="flex gap-1.5" id="tour-modal-dots"></div>
                    <button id="tour-modal-next" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-600/30 transition-all">
                        Next Step <i class="fas fa-chevron-right ml-1"></i>
                    </button>
                </div>
            </div>
        `,document.body.appendChild(g)}const t=document.getElementById("universal-hover-annotation-card"),n=document.getElementById("hover-card-step"),e=document.getElementById("hover-card-title"),i=document.getElementById("hover-card-desc"),o=document.getElementById("hover-card-action"),a=document.getElementById("guide-mode-toggle"),u=document.getElementById("start-tour-btn"),m=document.getElementById("tour-spotlight-modal"),h=document.getElementById("tour-modal-step"),p=document.getElementById("tour-modal-title"),c=document.getElementById("tour-modal-desc"),f=document.getElementById("tour-modal-tip"),v=document.getElementById("tour-modal-prev"),d=document.getElementById("tour-modal-next"),s=document.getElementById("tour-modal-close"),r=document.getElementById("tour-modal-dots");let l=localStorage.getItem("guide_mode_active")!=="false";document.body.classList.toggle("guide-mode-active",l),y();function y(){a&&(l?(a.classList.add("active"),a.innerHTML='<i class="fas fa-lightbulb text-amber-400"></i> <span>Guide: <strong class="text-white">ON</strong></span>'):(a.classList.remove("active"),a.innerHTML='<i class="far fa-lightbulb text-gray-400"></i> <span>Guide: <strong class="text-gray-300">OFF</strong></span>'))}a&&a.addEventListener("click",()=>{l=!l,localStorage.setItem("guide_mode_active",l),document.body.classList.toggle("guide-mode-active",l),y(),!l&&t&&t.classList.remove("visible"),S(l?"Interactive Guide Mode Enabled":"Guide Mode Disabled")});let b;document.querySelectorAll("[data-step-guide]").forEach(g=>{if(window.getComputedStyle(g).position==="static"&&(g.style.position="relative"),!g.querySelector(".interactive-beacon-pin")){const w=document.createElement("span");w.className="interactive-beacon-pin";const I=g.getAttribute("data-step-number")||"•";w.textContent=I.length<=4?I:"•",w.title=g.getAttribute("data-step-title")||"Interactive Feature",g.appendChild(w)}g.addEventListener("mouseenter",()=>{if(!l||!t)return;clearTimeout(b);const w=g.getAttribute("data-step-guide")||"",I=g.getAttribute("data-step-title")||"Interactive Feature",H=g.getAttribute("data-step-action")||"👉 Click to interact",G=g.getAttribute("data-step-number")||"01";n&&(n.textContent=`STEP ${G} • ONBOARDING GUIDE`),e&&(e.textContent=I),i&&(i.textContent=w),o&&(o.textContent=H);const P=g.getBoundingClientRect(),_=320,R=150;let M=P.left+P.width/2-_/2,D=P.top-R-12;M=Math.max(16,Math.min(M,window.innerWidth-_-16)),D<16&&(D=P.bottom+12),t.style.left=`${M}px`,t.style.top=`${D}px`,t.classList.add("visible")}),g.addEventListener("mouseleave",()=>{t&&(b=setTimeout(()=>{t.classList.remove("visible")},100))})});const T=window.location.pathname.toLowerCase();let x=[];T.includes("playground")?x=[{selector:'[data-step-number="PG-01"]',title:"Playground: API Gateway & Proxy",desc:"Check live connectivity to LiteLLM Proxy (:4000) or local Ollama (:11434). Click Settings to add custom API keys or fal.ai diffusion tokens.",tip:"💡 Pro-Tip: Zero setup required for local development."},{selector:'[data-step-number="PG-03"]',title:"Playground: Multimodal Modes",desc:"Switch fluidly between Chat, Dual-Model Comparison, FLUX Image Diffusion, and Generative AI Video rendering studios.",tip:"💡 Pro-Tip: All four studios remember your active configurations."},{selector:'[data-step-number="PG-04"]',title:"Playground: Neural Model Catalog",desc:"Select from available local or cloud LLM routers including deepseek-coder, llama3, and high-reasoning Kimi K3 & GLM-5.3.",tip:"💡 Pro-Tip: Click the refresh icon to scan for newly running local models."},{selector:'[data-step-number="PG-05"]',title:"Playground: System Role Presets",desc:"Fine-tune the assistant persona with built-in presets: Concise, Coder, Creative, or Socratic Tutor.",tip:"💡 Pro-Tip: Persona presets dynamically update prompt reasoning."},{selector:'[data-step-number="PG-06"]',title:"Playground: Hyperparameter Controls",desc:"Adjust Temperature, Top-P sampling, Max Tokens, and toggle live response streaming on or off.",tip:"💡 Pro-Tip: Set temperature low (0.2) for code, high (0.8) for brainstorming."},{selector:'[data-step-number="PG-07"]',title:"Playground: Prompt Input & Dice Generator",desc:"Write prompt instructions or click the 🎲 Random Prompt button to instantly test pre-curated prompts across engineering, science, and creative tasks.",tip:"💡 Pro-Tip: Works in Chat, Compare, Image, and Video modes!"}]:T.includes("blog")?x=[{selector:'[data-step-number="BL-01"]',title:"Research Hub: Instant Search",desc:"Quickly query across all research publications, architectural teardowns, and engineering benchmarks.",tip:'💡 Pro-Tip: Search terms like "Socratic", "Memory", or "Prompt Caching".'},{selector:'[data-step-number="BL-02"]',title:"Research Hub: Topic Categories",desc:"Filter articles by DeepTutor & Education, AI Agent Swarms, and Enterprise n8n Pipelines.",tip:"💡 Pro-Tip: Click any pill to filter in real time."},{selector:'[data-step-number="BL-03"]',title:"Research Hub: Flagship Research",desc:"Discover our flagship DeepTutor architecture breakdown comparing single LLM chat windows against lifelong cognitive companions.",tip:"💡 Pro-Tip: Links directly to live source code and web apps."}]:T.includes("deeptutor")?x=[{selector:'[data-step-number="DT-01"]',title:"DeepTutor: Live TutorBot Launch",desc:"Launch the deployed production TutorBot interface or clone the official repository directly into your local machine.",tip:"💡 Pro-Tip: Clone via git clone https://github.com/xennials-dev/DeepTutor.git"},{selector:'[data-step-number="DT-02"]',title:"DeepTutor: Cognitive Telemetry",desc:"Inspect real-time memory synchronization, active Socratic agent swarms, and local RAG document grounding with zero external data leaks.",tip:"💡 Pro-Tip: All embeddings run client-side or on private servers."},{selector:'[data-step-number="DT-03"]',title:"DeepTutor: Direct Project Connect",desc:"Copy git checkout commands or jump straight to GitHub issues and contributions.",tip:"💡 Pro-Tip: Click Copy Clone URL for instant clipboard copy."},{selector:'[data-step-number="DT-04"]',title:"DeepTutor: Socratic Simulator",desc:"Experience how TutorBot decomposes complex problems step-by-step using active Socratic inquiry instead of spoon-feeding direct answers.",tip:"💡 Pro-Tip: Select different academic domains to test."},{selector:'[data-step-number="HOS-01"]',title:"Hermes OS: Gateway & Brain Setup",desc:"Configure Hermes CLI and multi-channel messaging gateways (Telegram, Discord, Slack) with OpenRouter, Nous Portal, or Anthropic backends.",tip:'💡 Direction: Run "hermes setup" to link your API key and "hermes gateway setup" to connect channels.'},{selector:'[data-step-number="HOS-02"]',title:"Hermes OS: CodeGraph Indexing Engine",desc:"Integrate CodeGraph to pre-index repository symbols and AST maps, cutting token burn by 57% and eliminating 71% of tool calls.",tip:'💡 Direction: Run "codegraph install" then "codegraph init" in your codebase root.'},{selector:'[data-step-number="HOS-03"]',title:"Hermes OS: Mission Control & /steer Protocol",desc:"Decompose multi-week goals between human tasks and autonomous agent actions, using /steer to course-correct in flight.",tip:"💡 Direction: Type /steer in chat to adjust agent instructions without restarting conversations."},{selector:'[data-step-number="HOS-04"]',title:"Hermes OS: Efficiency Telemetry",desc:"Live verified benchmark stats comparing raw LLM recursive file reading against pre-indexed CodeGraph memory topology.",tip:"💡 Direction: CodeGraph saves an estimated 86% of tokens on large multi-file repositories."},{selector:'[data-step-number="HOS-05"]',title:"Hermes OS: Visual Document & Artifact Studio",desc:"Centralized document repository storing all generated invoices, code specs, HTML previews, and markdown briefs with 5-word titles and 14-word summaries.",tip:"💡 Direction: Filter by type, preview in modal, or use the interactive generator below."},{selector:'[data-step-number="HOS-06"]',title:"Hermes OS: 1-Click Prompt Arsenal",desc:"Instant copy-paste prompts to install the Document Management interface and link CodeGraph directly into Hermes Agent.",tip:"💡 Direction: Click Copy Prompt and paste directly into your Hermes terminal."}]:x=[{selector:'[data-step-number="01"]',title:"Step 1: Theme Personalization",desc:"Start by customizing the platform theme. Switch seamlessly between Indigo Cyber, Cyber Cyan & Emerald, or Deep Purple & Amber styles.",tip:"💡 Pro-Tip: Themes persist across all pages in local storage."},{selector:'[data-step-number="02"]',title:"Step 2: Instant Project Consultation",desc:"Use the primary action button to jump directly to our automated project intake and custom agent specification form.",tip:"💡 Pro-Tip: Ideal for businesses seeking zero-touch automation swarms."},{selector:'[data-step-number="03"]',title:"Step 3: Open Source Ecosystem",desc:"Explore our catalog of 379+ production repositories and flagship projects categorized into AI Agents, Full Stack, and Automations.",tip:"💡 Pro-Tip: Click Quick View on any project card to see tech stack breakdowns."},{selector:'[data-step-number="04"]',title:"Step 4: Autonomous Workflows Hub",desc:"Navigate through our 4 core architecture tabs: 6-Stage Video Pipeline, 7-Agent Workforce Matrix, API Cost Optimizer, and Client Onboarding Engine.",tip:"💡 Pro-Tip: Each tab offers production-ready architectural schemas."},{selector:'[data-step-number="05"]',title:"Step 5: Multi-Agent Execution Simulator",desc:"Test our 6-stage video automation pipeline in real time. Enter any topic keyword and watch research, scripting, voiceover, and video rendering stream in live logs.",tip:"💡 Pro-Tip: Demonstrates zero-touch content pipeline capabilities."},{selector:'[data-step-number="06"]',title:"Step 6: Real-Time API Cost Optimizer",desc:"Adjust the monthly job slider and toggle Prompt Caching and Smart Model Routing to see how per-video costs drop from $2.10 down to $0.46 (78% margin).",tip:"💡 Pro-Tip: Shows how tiered LLM routing maximizes ROI."},{selector:'[data-step-number="07"]',title:"Step 7: Team Automation ROI Calculator",desc:"Calculate annual hours recovered and gross dollar savings when deploying Xennials AI automations across your team size.",tip:"💡 Pro-Tip: Adjust manual hours per person to match your team workflows."},{selector:'[data-step-number="08"]',title:"Step 8: Deploy Custom AI Infrastructure",desc:"Submit your specific technical requirements and our team will design, test, and deploy customized autonomous agent swarms for your organization.",tip:"💡 Pro-Tip: Responses are typically delivered within 24 hours."}];let E=0;function L(){r&&(r.innerHTML="",x.forEach((g,A)=>{const w=document.createElement("div");w.className=`w-2 h-2 rounded-full transition-all ${A===E?"bg-indigo-500 w-5":"bg-slate-700"}`,r.appendChild(w)}))}function k(g){if(g<0||g>=x.length)return;E=g,document.querySelectorAll(".tour-step-highlight").forEach(I=>I.classList.remove("tour-step-highlight"));const A=x[E],w=document.querySelector(A.selector);w&&(w.classList.add("tour-step-highlight"),w.scrollIntoView({behavior:"smooth",block:"center"})),h&&(h.textContent=`STEP ${E+1} OF ${x.length}`),p&&(p.textContent=A.title),c&&(c.textContent=A.desc),f&&(f.textContent=A.tip),v&&(v.disabled=E===0),v&&(v.style.opacity=E===0?"0.4":"1"),d&&(E===x.length-1?(d.innerHTML='Finish Tour <i class="fas fa-check ml-1"></i>',d.className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-emerald-600/30 transition-all"):(d.innerHTML='Next Step <i class="fas fa-chevron-right ml-1"></i>',d.className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-600/30 transition-all")),L(),m&&m.classList.add("active")}function B(){m&&m.classList.remove("active"),document.querySelectorAll(".tour-step-highlight").forEach(g=>g.classList.remove("tour-step-highlight"))}u&&u.addEventListener("click",()=>{k(0)}),d&&d.addEventListener("click",()=>{E>=x.length-1?(B(),S("Guided Tour Complete! Enjoy exploring Xennials.")):k(E+1)}),v&&v.addEventListener("click",()=>{E>0&&k(E-1)}),s&&s.addEventListener("click",B),m&&m.addEventListener("click",g=>{g.target===m&&B()}),document.addEventListener("keydown",g=>{!m||!m.classList.contains("active")||(g.key==="Escape"&&B(),g.key==="ArrowRight"&&E<x.length-1&&k(E+1),g.key==="ArrowLeft"&&E>0&&k(E-1))})}function se(){const t=document.querySelectorAll(".cinema-tab-btn"),n=document.getElementById("stage-core"),e=document.getElementById("stage-autopilot"),i=document.getElementById("cinema-frame"),o=document.getElementById("cinema-auto-cycle-btn"),a=document.getElementById("cinema-cycle-status"),u=document.getElementById("cinema-cycle-icon"),m=document.getElementById("cinema-interactive-space");if(!n||!e)return;let h="core",p=!0,c=null;function f(s){h=s,t.forEach(r=>{r.getAttribute("data-stage")===s?(r.classList.add("active","text-amber-200","bg-amber-500/20","border-amber-500/30"),r.classList.remove("text-gray-400")):(r.classList.remove("active","text-amber-200","bg-amber-500/20","border-amber-500/30"),r.classList.add("text-gray-400"))}),s==="core"?(e.classList.add("hidden"),e.classList.remove("active"),n.classList.remove("hidden"),setTimeout(()=>n.classList.add("active"),50)):(n.classList.add("hidden"),n.classList.remove("active"),e.classList.remove("hidden"),setTimeout(()=>e.classList.add("active"),50))}t.forEach(s=>{s.addEventListener("click",()=>{const r=s.getAttribute("data-stage");r&&f(r)})});function v(){c&&clearInterval(c),c=setInterval(()=>{if(!p)return;f(h==="core"?"autopilot":"core")},7e3)}function d(){c&&clearInterval(c),c=null}o&&o.addEventListener("click",()=>{p=!p,p?(a.textContent="ON",a.className="text-emerald-400",u.className="fas fa-play text-emerald-400 text-[10px]",v()):(a.textContent="OFF",a.className="text-gray-400",u.className="fas fa-pause text-gray-400 text-[10px]",d())}),i&&(i.addEventListener("mouseenter",()=>{p&&d()}),i.addEventListener("mouseleave",()=>{p&&v(),m&&(m.style.transform="perspective(1000px) rotateX(0deg) rotateY(0deg)")}),i.addEventListener("mousemove",s=>{if(!m)return;const r=i.getBoundingClientRect(),l=s.clientX-r.left-r.width/2,y=s.clientY-r.top-r.height/2,b=-y/r.height*8,C=l/r.width*8;m.style.transform=`perspective(1000px) rotateX(${b.toFixed(2)}deg) rotateY(${C.toFixed(2)}deg)`,m.querySelectorAll(".cinema-hud-card").forEach((x,E)=>{const L=(E+1)*3;x.style.transform=`translate3d(${l/40*L}px, ${y/40*L}px, ${L*4}px)`})})),v()}function ae(){const t=document.querySelectorAll(".doc-filter-btn"),n=document.getElementById("hermes-document-grid"),e=document.getElementById("hermes-doc-modal"),i=document.getElementById("modal-doc-title"),o=document.getElementById("modal-doc-content"),a=document.getElementById("modal-doc-path"),u=document.getElementById("close-hermes-modal-btn"),m=document.getElementById("modal-copy-btn"),h=document.getElementById("hermes-generate-doc-btn"),p=document.getElementById("hermes-new-doc-prompt");if(!n)return;const c={"doc-1":{title:"Enterprise Client Invoice Template",path:"assets/invoices/invoice_dana_ufc_50k.html",content:`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Invoice #XEN-2026-8842</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px; }
    .invoice-card { max-width: 680px; margin: 0 auto; background: #131b2e; border: 1px solid #334155; border-radius: 16px; padding: 32px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
    .header { display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 20px; }
    .gold-brand { color: #fbbf24; font-weight: 800; font-size: 20px; letter-spacing: 1px; }
    .bill-to { margin: 24px 0; font-size: 14px; color: #94a3b8; }
    .total-due { font-size: 28px; font-weight: 700; color: #10b981; margin-top: 16px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { text-align: left; padding: 12px; border-bottom: 1px solid #1e293b; font-size: 13px; }
    th { color: #6366f1; text-transform: uppercase; font-size: 11px; }
  </style>
</head>
<body>
  <div class="invoice-card">
    <div class="header">
      <div>
        <div class="gold-brand">XENNIALS AI AGENT CORP</div>
        <p style="font-size: 12px; color: #64748b;">Autonomous Agent Workforce Engineering</p>
      </div>
      <div style="text-align: right; font-size: 12px; color: #94a3b8;">
        <strong>INVOICE #XEN-2026-8842</strong><br>
        Date: August 30, 2026<br>
        Due: Upon Receipt
      </div>
    </div>
    
    <div class="bill-to">
      <strong style="color: #fff;">Billed To:</strong><br>
      Dana White • Ultimate Fighting Championship (UFC)<br>
      6650 S Torrey Pines Dr, Las Vegas, NV 89118
    </div>

    <table>
      <thead>
        <tr><th>Description</th><th>Hours / Scope</th><th>Rate</th><th>Amount</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>Autonomous Agent Workforce & LangGraph State Machine Architecture</td>
          <td>Tier 1 Enterprise Spec</td>
          <td>$50,000</td>
          <td style="color: #10b981; font-weight: 600;">$50,000.00</td>
        </tr>
      </tbody>
    </table>

    <div style="text-align: right; margin-top: 24px;">
      <span style="font-size: 12px; color: #64748b;">TOTAL BALANCE DUE</span>
      <div class="total-due">$50,000.00 USD</div>
    </div>
  </div>
</body>
</html>`},"doc-2":{title:"CodeGraph Repository Knowledge Map",path:".codegraph/schema.json",content:`{
  "codegraph_version": "2.4.1",
  "project_root": "c:/Users/tee/scratch/xennials-web",
  "total_symbols": 842,
  "indexed_files": 48,
  "metrics": {
    "token_reduction_ratio": 0.574,
    "tool_call_efficiency": 0.712,
    "ast_scan_time_ms": 142
  },
  "dependency_nodes": [
    { "file": "playground-engine.js", "imports": ["script.js", "styles.css"], "exports": ["TASK_TAXONOMY_MAP", "bindTaxonomyModalAndTasks"] },
    { "file": "script.js", "imports": ["styles.css"], "exports": ["initGuidedAnnotationsAndTour", "initHermesDocumentStudio"] },
    { "file": "deeptutor.html", "renders": ["#hermes-document-grid", "#hermes-doc-modal"] }
  ],
  "symbol_references": {
    "bindTaxonomyModalAndTasks": { "callers": ["init"], "line": 1354, "complexity": 3 },
    "initHermesDocumentStudio": { "callers": ["DOMContentLoaded"], "line": 1668, "complexity": 4 }
  }
}`},"doc-3":{title:"Mission Control 30-Day Growth Goal",path:"goals/growth_strategy.md",content:`# Mission Control • 30-Day YouTube 1,000 Subscriber Roadmap

## High-Level Objective
Scale Xennials Developer YouTube channel from 0 to 1,000 active engineering subscribers in 30 days utilizing autonomous Hermes research and production workflows.

---

### Phase 1: Shared Task Allocation

#### 👤 Human Creator Tasks
- Record 4 high-fidelity Loom architectural walkthroughs (10-15 mins).
- Deliver personal voice commentary on real startup AI automation case studies.
- Approve final video edits rendered by the pipeline.

#### 🤖 Hermes Autonomous Agent Tasks
- Run nightly deep research on trending LangGraph and AI Agent search queries.
- Draft 12 SEO-optimized YouTube video scripts with hook formulas and timestamps.
- Generate 3 high-CTR thumbnail concept prompts for Flux diffusion.
- Transcribe and auto-generate clean video description markdown with GitHub links.

---

### Phase 2: Live /steer Commands
- Use \`/steer\` during script creation to pivot tone towards enterprise developers:
  \`\`\`bash
  /steer adjust script to focus on 57% token reduction with CodeGraph and live CLI benchmarks
  \`\`\`
`},"doc-4":{title:"Nightly Dream Insights Brief",path:"dreams/brief_2026_08_30.json",content:`{
  "dream_run_id": "drm_20260830_040000",
  "synthesized_sources": [
    "Claude Code Terminal Sessions (14 turns)",
    "Hermes CLI Logs (28 turns)",
    "AntiGravity IDE Transcripts (62 steps)"
  ],
  "key_insights": [
    {
      "category": "Cost Optimization",
      "severity": "HIGH_IMPACT",
      "finding": "Claude 3.5 Sonnet was used for 42 mechanical regex string formatting tasks that Hermes MiMo / DeepSeek could execute for $0.00.",
      "actionable_recommendation": "Route parsing jobs to Mercury persona on local Ollama, saving ~$420/month."
    },
    {
      "category": "Code Repetition",
      "severity": "MEDIUM_IMPACT",
      "finding": "Discovered 4 redundant file scans across /scripts directory before CodeGraph was initialized.",
      "actionable_recommendation": "Enabled auto-sync hook in .codegraph/config.yaml to maintain zero-cost AST state."
    }
  ],
  "morning_brief_summary": "Good morning! Your agentic operating system ran for 4 hours overnight. CodeGraph is synchronized, and 3 model routing shortcuts were staged to reduce your daily API burn."
}`},"doc-5":{title:"Athena Strategic Architectural Spec",path:"pantheon/athena_spec.py",content:`"""
Athena Strategic Persona Specification
Xennials Agentic Operating System • Role-Based Swarm Dispatch
"""

from typing import Dict, Any

ATHENA_CONFIG: Dict[str, Any] = {
    "persona_name": "Athena",
    "domain": "Strategic Architecture & LangGraph State Machines",
    "preferred_model": "claude-3-7-sonnet-thought",
    "fallback_model": "deepseek-reasoner",
    "system_prompt": (
        "You are Athena, the Chief AI Systems Architect of the Xennials workforce. "
        "Your mission is to decompose complex human business objectives into fault-tolerant, "
        "asynchronous multi-agent state machines. Enforce zero token waste, structured schema output, "
        "and deterministic failover mechanisms at every graph node."
    ),
    "max_context_window": 128000,
    "temperature": 0.2,
    "mcp_tools_enabled": [
        "codegraph_query",
        "doc_manager_store",
        "langgraph_validator"
    ]
}
`},"doc-6":{title:"Automated Expense Telemetry Data",path:"analytics/spend_matrix.html",content:`<!-- Real-Time AI Spend & Token Telemetry Dashboard -->
<div class="telemetry-grid" style="font-family: monospace; color: #e2e8f0;">
  <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 8px;">
    <span>PLATFORM</span>
    <span>DAILY TOKENS</span>
    <span>COST (USD)</span>
    <span>EFFICIENCY STATUS</span>
  </div>
  <div style="display: flex; justify-content: space-between; padding: 8px 0; color: #38bdf8;">
    <span>Claude Code CLI</span>
    <span>420,500</span>
    <span>$1.26</span>
    <span style="color: #10b981;">OPTIMIZED (-57% via CodeGraph)</span>
  </div>
  <div style="display: flex; justify-content: space-between; padding: 8px 0; color: #fbbf24;">
    <span>Hermes Agent Swarm</span>
    <span>1,240,000</span>
    <span>$0.38</span>
    <span style="color: #10b981;">HIGH ROI (MiMo & OpenRouter)</span>
  </div>
  <div style="display: flex; justify-content: space-between; padding: 8px 0; color: #ec4899;">
    <span>AntiGravity IDE</span>
    <span>890,200</span>
    <span>$0.00</span>
    <span style="color: #38bdf8;">TIER 1 (Built-in Workspace)</span>
  </div>
</div>`}};t.forEach(d=>{d.addEventListener("click",()=>{t.forEach(l=>{l.classList.remove("active","bg-indigo-600","text-white"),l.classList.add("bg-slate-900","text-gray-300")}),d.classList.add("active","bg-indigo-600","text-white"),d.classList.remove("bg-slate-900","text-gray-300");const s=d.dataset.docType;n.querySelectorAll(".hermes-doc-card").forEach(l=>{const y=l.dataset.type;s==="all"||y===s?l.style.display="flex":l.style.display="none"})})});function f(){const d=n.querySelectorAll(".view-doc-btn"),s=n.querySelectorAll(".copy-doc-btn"),r=n.querySelectorAll(".delete-doc-btn");d.forEach(l=>{l.onclick=()=>{const y=l.dataset.docId,b=c[y]||{title:l.closest(".hermes-doc-card").querySelector("h4").textContent,path:"assets/documents/custom_doc.txt",content:"Generated Document Content synchronized with Hermes Agent Workspace."};i&&(i.textContent=b.title),a&&(a.textContent=b.path),o&&(o.textContent=b.content),m&&(m.onclick=()=>{navigator.clipboard.writeText(b.content),S("Document content copied to clipboard!")}),e&&e.classList.remove("hidden")}}),s.forEach(l=>{l.onclick=()=>{const y=l.closest(".hermes-doc-card"),b=y.querySelector("h4").textContent,C=y.querySelector("p").textContent;navigator.clipboard.writeText(`${b}
${C}`),S("Document metadata copied to clipboard!")}}),r.forEach(l=>{l.onclick=()=>{const y=l.closest(".hermes-doc-card"),b=y.querySelector("h4").textContent;y.style.transition="all 0.3s ease",y.style.transform="scale(0.9)",y.style.opacity="0",setTimeout(()=>{y.remove(),v(),S(`Deleted document: ${b}`)},300)}})}function v(){const d=n.querySelectorAll(".hermes-doc-card"),s=document.getElementById("count-all");s&&(s.textContent=d.length)}u&&e&&(u.onclick=()=>e.classList.add("hidden"),e.onclick=d=>{d.target===e&&e.classList.add("hidden")}),h&&p&&(h.onclick=()=>{const d=p.value.trim();if(!d){S("Please enter a document prompt or invoice scenario.");return}const s=d.split(/\s+/),r=s.slice(0,5).join(" ").replace(/[^\w\s]/g,"")||"New Autonomous Generated Document",l=s.slice(0,14).join(" ")||"Custom document generated in real-time by Hermes Agent and saved to workspace.",y=`doc-custom-${Date.now()}`;c[y]={title:r,path:`assets/generated/${r.toLowerCase().replace(/\s+/g,"_")}.html`,content:`<!-- Hermes Agent Generated Document -->
<!-- Prompt: ${d} -->

<div class="generated-artifact">
  <h2>${r}</h2>
  <p>${l}</p>
  <p>Generated at: ${new Date().toLocaleString()}</p>
  <p>Status: Synchronized with Hermes Workspace</p>
</div>`};const b=document.createElement("div");b.className="hermes-doc-card animate-fadeIn",b.dataset.type="html",b.innerHTML=`
                <div>
                    <div class="flex items-center justify-between mb-3">
                        <span class="hermes-doc-tag doc-tag-html"><i class="fas fa-magic"></i> AI Generated</span>
                        <span class="text-[10px] text-gray-500 font-mono">Just Now</span>
                    </div>
                    <h4 class="font-bold font-space text-white text-base mb-2">${r}</h4>
                    <p class="text-xs text-gray-400 mb-4 leading-relaxed">${l}</p>
                </div>
                <div class="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs">
                    <span class="text-gray-500 font-mono text-[10px]">${c[y].path}</span>
                    <div class="flex gap-2">
                        <button class="px-2.5 py-1 bg-slate-800 hover:bg-indigo-600 rounded text-gray-300 hover:text-white font-mono view-doc-btn" data-doc-id="${y}">View</button>
                        <button class="px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded text-gray-400 hover:text-white copy-doc-btn" title="Copy Content"><i class="fas fa-copy"></i></button>
                        <button class="px-2 py-1 bg-slate-800 hover:bg-red-950/80 rounded text-gray-400 hover:text-red-400 delete-doc-btn" title="Delete"><i class="fas fa-trash-alt"></i></button>
                    </div>
                </div>
            `,n.prepend(b),p.value="",f(),v(),S(`Hermes Agent Generated Document: "${r}"`)}),f()}
