"""Pivots/rebrands manually CURATED from the stitched detector.

Each entry is a MANUAL judgment (I read the titles/h1/content of the snapshots
in the months of greatest variation and at the domain boundaries) about whether
there was a product PIVOT or a REBRAND, with the date pinned down via Wayback.
The `domain`+`date` fields are used to resolve the exact snapshot (wayback_url)
that becomes the SOURCE of the chip on the site.

Output: data/pivots_curated.json
"""
from __future__ import annotations
import json
import common

# (slug, type, date YYYY-MM, domain-to-resolve, title, prose)
# type: "rebrand" (changed the name) | "pivot" (changed the product, same name)
CURATED = [
 # ---- REBRANDS (name change), date = first evidence of the new brand in Wayback ----
 ("cardda","pivot","2020-10","cardda.com","De Rentz a Cardda",
  "El equipo venía de Rentz (arriendo de maquinaria pesada, rentz.cl); a fines de 2020 lanzó Cardda, contratación de servicios online con factura para empresas."),
 ("repartes","rebrand","2025-04","partsflow.ai","De Repartes a Partsflow",
  "Repartes (marketplace B2B de repuestos, repartes.com) se relanzó como Partsflow: CRM con agentes de IA para automatizar la venta de repuestos por WhatsApp."),
 ("pipoll","pivot","2023-06","pulsoescolar.cl","Consolidación en Pulso Escolar",
  "La razón social Pipoll operó la marca B2B (engagement de colaboradores) en paralelo a Pulso Escolar (cultura escolar); el negocio se consolidó bajo Pulso Escolar."),
 ("morfy","rebrand","2021-12","morfy.app","De El Club del Bajón a Morfy",
  "Nació como 'El Club del Bajón' (clubdelbajon.com, publicidad/gastronomía); rebranding a Morfy, la app de recomendaciones gastronómicas, a fines de 2021."),
 ("utomata","rebrand","2024-03","fireflux.app","De Utomata a Fireflux",
  "El codename interno era Utomata; para el primer landing público (fireflux.app, marzo 2024) ya operaba como Fireflux, no-code + IA para operaciones de campo."),
 ("payhaus","rebrand","2023-05","unifyr.ai","De Payhaus a Unifyr",
  "Payhaus (salario devengado, payhaus.app) pivoteó a analítica y se renombró Unifyr (unifyr.ai) en mayo 2023 antes de cesar operaciones."),
 ("telaio","rebrand","2023-10","getlummy.com","De Telaio/Kapibara a Lummy",
  "Telaio Finance (software contable) → Kapibara (seguridad infantil) → en octubre 2023 lanzó Lummy, app de salud mental (getlummy.com)."),
 ("telaio","pivot","2024-08","lummy.ai","Lummy pasa a B2B (Lummy.ai)",
  "El producto consumer de salud mental viró a un chatbot de IA B2B para atención al cliente y ventas (lummy.ai); más adelante se enfocó en clínicas."),
 ("grandpa","rebrand","2025-07","bloocks.com","De Manifest a Bloocks",
  "Manifest (crear apps desde un prompt, manifest-hq.com) se renombró Bloocks a mediados de 2025; manifest-hq.com redirige a bloocks.com, hoy dominio en venta."),
 ("fudata","rebrand","2023-09","appio.ai","De Fudata a Appio",
  "Fudata (marcas de restaurantes basadas en datos, fudata.com.mx) se consolidó como Appio (appio.ai): crecimiento/delivery por WhatsApp para restaurantes."),
 ("pronty","rebrand","2024-06","blokay.com","De Pronty/Sigfre a Blokay",
  "El equipo pasó por Pronty (pronty.co) y Sigfre antes de relanzarse como Blokay (jun-2024): dashboards, backoffices y APIs en segundos. Mismos fundadores (Daniela Garzón, Juan David Restrepo)."),
 ("salduu","rebrand","2024-05","profile:salduu","De Profe.Social a Salduu",
  "Antes era Profe.Social (plataforma para profesores); el mismo equipo (CEO Angelo López Espíndola, Profe Social SpA) se relanzó como Salduu: plataforma para vender productos y servicios digitales."),
 ("verso","rebrand","2024-02","getcarttera.com","De Verso a Carttera",
  "Verso (Verso Technologies, verso.ai, agenda/cobros para independientes) se renombró Carttera (cobros y conciliación por WhatsApp) antes de cerrar."),
 ("unacuarta","rebrand","2025-07","caudal.app","De UnaCuarta a Caudal",
  "El mismo equipo pivoteó de proptech (inversión inmobiliaria fraccionada, unacuarta.com) a logística de agua: Caudal (caudal.app), mediados de 2025."),
 ("auth4all","rebrand","2024-02","identyz.com","De Autentiz a Identyz",
  "Autentiz (verificación de identidad, autentiz.com) se renombró Identyz; autentiz.com redirige a identyz.com. La razón social Autentiz SpA se mantuvo."),
 ("wireworks","rebrand","2023-12","getperhaps.com","De Wireworks a Perhaps",
  "Wireworks (flujos colaborativos desde grabaciones, wireworks.app) se renombró Perhaps (getperhaps.com), un studio AI-native."),
 ("wireworks","pivot","2025-05","faces.app","Perhaps lanza Faces",
  "Tras iterar (Workspace, Workers, Interfaces), el producto se centró en Faces (faces.app): presentaciones interactivas."),
 ("strade","rebrand","2022-07","stradeworld.com","De Viking Studio a Strade",
  "Viking Studio (sneakers custom + NFTs) se renombró Strade; para 2022 operaba como Strade World."),
 ("strade","pivot","2023-08","stradeworld.com","Strade 2.0: reventa de lujo",
  "Pasó de sneakers custom + NFTs a un marketplace de reventa y autenticación de productos de lujo (Strade 2.0)."),
 # ---- Product PIVOTS (same name), date = first evidence of the new focus ----
 ("bircle","pivot","2023-12","bircle.io","De Phygital a BircleAI",
  "Bircle empezó como 'Phygital' (marketplace NFT de prendas físico-digitales) y pivoteó a agentes de IA para relacionamiento con clientes (cobranza/ventas/atención)."),
 ("altur","pivot","2025-04","altur.io","De chatbots a agentes de voz IA",
  "Altur pasó de chatbots de cobranza por WhatsApp a agentes de Voz con IA (telefonía propia) para cobranza y ventas."),
 ("plutto","pivot","2025-06","getplutto.com","De KYB a riesgo de terceros",
  "Plutto amplió de background-check de empresas (KYB) a una plataforma de evaluación y gestión de riesgo de terceros / compliance."),
 ("blar","pivot","2024-07","blar.io","De NL2SQL a encontrar la causa raíz de bugs",
  "Blar nació como un 'ChatGPT para datos financieros' (NL2SQL; su paper Blar-SQL es de ene-2024). Pivoteó a entender el código: representa el repositorio como un grafo que un agente recorre para encontrar la causa raíz de bugs y errores."),
 ("blar","pivot","2024-11","blar.io","De depurar bugs a gestionar deuda técnica",
  "Con su grafo del código, Blar pasó a actuar como un desarrollador senior automatizado: detecta y prioriza deuda técnica, propone arreglos y revisa los pull requests antes de que lleguen al equipo."),
 ("blar","pivot","2025-10","blar.io","De herramienta para devs a soporte de usuarios con IA",
  "Último pivot: Blar dejó las herramientas para developers y se volcó al soporte de usuarios. Hoy es un agente de IA que vive dentro del producto del cliente y usa el conocimiento del código y la documentación para resolver tickets de soporte y guiar al usuario por la interfaz."),
 ("gokei","pivot","2024-09","getgokei.com","De gestión de salud a reembolsos automáticos",
  "Empezó como una app amplia para coordinar la salud (agendar horas, exámenes, medicamentos) e incluso evaluó vender un seguro complementario. Tras el programa se enfocó en lo que más usaban sus usuarios: el reembolso automático de gastos médicos ante isapres y seguros."),
 ("gokei","rebrand","2026-01","getskip.ai","De Gokei a Skip",
  "A inicios de 2026 Gokei se renombró Skip y sumó un copago virtual ('atiéndete ahora, paga después'): el paciente paga solo el 30% de la prestación y Skip adelanta el resto, cobrándolo cuando llega el reembolso. Respaldada por fundadores de Cornershop."),
 ("kapso","pivot","2025-03","kapso.ai","De personal training con IA a WhatsApp para developers",
  "Kapso nació como personal training online: una sesión inicial con un coach humano y luego rutinas de fuerza personalizadas con IA vía app (prensa, may-2024). A inicios de 2025 pivoteó por completo a infraestructura de WhatsApp para developers: API y agentes de IA para sumar WhatsApp a cualquier producto."),
 ("felz","pivot","2025-11","tiendasfelz.com","De SaaS a operar mini-markets",
  "Felz pasó de SaaS para tienditas a adquirir y operar su propia red de mini-markets híper-locales."),
 # ---- Segunda pasada (auditoría title-timeline sobre las 82): pivots/rebrands sub-capturados ----
 ("watermelon-tools","pivot","2022-01","watermelon.tools","De cultura de equipo a entender el código",
  "Watermelon partió como una app de Slack para conectar compañeros por intereses en común y mejorar la cultura de los equipos remotos. A inicios de 2022 pivoteó por completo a una herramienta para developers: dentro de VS Code muestra el contexto histórico de cualquier trozo de código —rastreando GitHub y Slack— y responde dudas en lenguaje simple."),
 ("fintoc","pivot","2023-02","fintoc.com","De API de datos bancarios a pagos",
  "Fintoc partió como una API de open banking para conectar cuentas y leer balances y movimientos. A inicios de 2023 sumó su negocio principal: la iniciación de pagos —que los usuarios transfieran sin salir de la app del cliente—, más débito directo y conciliación bancaria automática."),
 ("elcerokm","pivot","2025-04","elcerokm.com","De comparador de precios a marketplace de autos 0km",
  "ElCeroKm empezó como un sitio para consultar el precio real de los autos 0km en Argentina y evitar sobreprecios. En 2025 pasó a un marketplace transaccional: comparar y comprar el auto nuevo online, sin moverse de la casa."),
 ("fraccional","rebrand","2023-01","fraccional.cl","De Urvana a Fraccional",
  "El equipo venía de Urvana: valorización y compra/venta de suelo para proyectos inmobiliarios. A inicios de 2023 lanzó Fraccional, su producto principal: invertir en fracciones de propiedades, sin créditos ni trámites."),
 ("cardda","pivot","2021-05","cardda.com","De contratar servicios a tarjetas para startups",
  "Ya como Cardda (contratar servicios SaaS para empresas desde un solo lugar), a mediados de 2021 viró a emitir tarjetas virtuales al instante para que las startups controlaran sus pagos y suscripciones."),
 ("cacttus","pivot","2022-10","cacttus.cl","De seguro digital a seguro de mascotas",
  "Cacttus partió como un seguro digital de contratación instantánea (cotizas y te suscribes en segundos, con posventa rápida). Se enfocó en un nicho: el seguro de salud para mascotas, con reembolsos en minutos (y seguro de auto en camino)."),
 ("wayak","pivot","2024-05","wayak.io","De app social a plataforma de agentes de IA",
  "Wayak partió como una app social para registrar el avance de tus metas e ideas en una línea de tiempo y motivarte junto a una comunidad. En 2024 se reinventó como una plataforma para crear y orquestar agentes de IA: defines cada agente (nombre, propósito y tarea), los combinas en equipos y eliges el modelo (LLM) para cada uno."),
 ("flair","pivot","2024-03","goflair.cl","De medidor de CO2 a ahorro energético HVAC",
  "Flair partió como un medidor de calidad del aire / CO2 (Airly). Pivoteó a la eficiencia energética de edificios: un sistema plug-and-play que retrofittea y optimiza el aire acondicionado (HVAC) para reducir hasta 30% del consumo."),
 ("brolly","pivot","2022-12","brolly.cl","De gestión de remuneraciones a créditos digitales",
  "Brolly partió como una plataforma de gestión de remuneraciones y RRHH para empresas, con créditos y beneficios para empleados como complemento. Pivoteó a fintech: créditos digitales de bajo costo y educación financiera para los trabajadores."),
 ("larnu","pivot","2022-06","larnu.com","De upskilling profesional a aprender a programar",
  "LarnU partió como una app de upskilling profesional gamificado (cursos de carrera, incluso de web3 y cripto, en 10 minutos al día). Se enfocó en enseñar a programar: el 'Duolingo para programar', con lecciones y proyectos cortos."),
]


def resolve_wayback(domain: str, date: str) -> tuple[str | None, str | None]:
    """Returns (timestamp, view_url) of the snapshot for the month `date` (or the closest one).
    `domain` can be a domain (data/wayback/<dom>) or 'profile:<slug>' for the
    Platanus profile (data/wayback_platanus/<slug>)."""
    if domain.startswith("profile:"):
        mf = common.DATA_DIR / "wayback_platanus" / domain.split(":", 1)[1] / "manifest.json"
    else:
        mf = common.DATA_DIR / "wayback" / domain / "manifest.json"
    if not mf.exists():
        return None, None
    snaps = json.loads(mf.read_text(encoding="utf-8")).get("snapshots", [])
    snaps = [s for s in snaps if s.get("timestamp")]
    if not snaps:
        return None, None
    target = date.replace("-", "")  # YYYYMM
    # snapshot whose YYYYMM == target, otherwise the first >= target, otherwise the last
    exact = [s for s in snaps if s["timestamp"][:6] == target]
    pick = exact[0] if exact else next((s for s in snaps if s["timestamp"][:6] >= target), snaps[-1])
    return pick["timestamp"], pick.get("wayback_url")


def main() -> None:
    out = []
    for slug, typ, date, domain, title, prose in CURATED:
        ts, url = resolve_wayback(domain, date)
        out.append({"slug": slug, "type": typ, "date": date, "domain": domain,
                    "title": title, "prose": prose,
                    "wayback_ts": ts, "wayback_url": url})
        flag = "" if url else "  ⚠ sin snapshot"
        print(f"  {slug:14} {typ:8} {date}  {domain:22} ts={ts}{flag}")
    (common.DATA_DIR / "pivots_curated.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✔ {len(out)} pivots/rebrands curados → data/pivots_curated.json")
    print(f"  con wayback_url: {sum(1 for o in out if o['wayback_url'])}/{len(out)}")


if __name__ == "__main__":
    main()
