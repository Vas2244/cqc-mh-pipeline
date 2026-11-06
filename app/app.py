import altair as alt
import duckdb
import streamlit as st

st.set_page_config(page_title="London's mental health services", layout="wide")

# colours: each one means one thing everywhere
# purple = NHS, pink = independent, grey = other, amber = none registered locally
COLOURS = {"NHS": "#5B2A86", "Independent": "#C2185B", "Other": "#8E8A99"}
PURPLE = COLOURS["NHS"]
PINK = COLOURS["Independent"]
AMBER = "#D98E04"
MUTED = "#E9D7B0"  # pale amber, for the bars that aren't the point

# shorter labels for CQC's specialism names, so the charts are readable (display only)
SHORT = {
    "Caring for adults under 65 yrs": "Adults under 65",
    "Caring for adults over 65 yrs": "Older adults (65+)",
    "Mental health conditions": "Mental health conditions",
    "Substance misuse problems": "Substance misuse",
    "Caring for people whose rights are restricted under the Mental Health Act": "Mental Health Act",
    "Caring for children": "Children and young people",
    "Eating disorders": "Eating disorders",
    "Learning disabilities": "Learning disabilities",
    "Dementia": "Dementia",
    "Services for everyone": "Services for everyone",
    "Physical disabilities": "Physical disabilities",
    "Sensory impairment": "Sensory impairment",
}

SNAPSHOT = "6 Nov 2026"  # the day the raw data was pulled from the CQC API


# ---------- load the data ----------
# the app only reads mart tables. All the counting is done in sql/03_mart.sql,
# so every number shown here is built (and tested) in SQL. The app just displays it.
con = duckdb.connect("data/cqc.duckdb", read_only=True)
services = con.sql("SELECT * FROM mart_services").df()                    # finder, map, table
summary = con.sql("SELECT * FROM mart_summary").df().iloc[0]              # big numbers
borough_run_by = con.sql("SELECT * FROM mart_borough_run_by").df()        # borough chart
specialism_run_by = con.sql("SELECT * FROM mart_specialism_run_by").df()  # who runs each type
icb_run_by = con.sql("SELECT * FROM mart_icb_run_by").df()                # who runs each ICB
gaps = con.sql("SELECT * FROM mart_gaps").df()                            # gaps grid
gaps_summary = con.sql("SELECT * FROM mart_gaps_summary").df()            # boroughs with none
con.close()

# display only: short labels, colours, and the order the bars stack in
for table in [specialism_run_by, gaps, gaps_summary]:
    table["specialism"] = table["specialism"].map(SHORT)
services["colour"] = services["run_by"].map(COLOURS)
for table in [borough_run_by, specialism_run_by, icb_run_by]:
    table["stack"] = table["run_by"].map({"NHS": 0, "Independent": 1, "Other": 2})
# the bars to highlight in the gaps chart
gaps_summary["highlight"] = gaps_summary["specialism"].isin(["Eating disorders", "Children and young people"])
none_per_need = gaps_summary.set_index("specialism")["boroughs_with_none"]


def look_up(table, field, value, run_by):
    # reads one number straight from a mart table (0 if that row doesn't exist)
    row = table[(table[field] == value) & (table["run_by"] == run_by)]
    return int(row["services"].iloc[0]) if len(row) else 0


# numbers used in the text, all read from the mart
nhs = int(summary["nhs"])
independent = int(summary["independent"])
pct_independent = int(summary["pct_independent"])
no_eating = int(none_per_need["Eating disorders"])
no_children = int(none_per_need["Children and young people"])
substance_ind = look_up(specialism_run_by, "specialism", "Substance misuse", "Independent")
substance_nhs = look_up(specialism_run_by, "specialism", "Substance misuse", "NHS")
dementia_nhs = look_up(specialism_run_by, "specialism", "Dementia", "NHS")
dementia_ind = look_up(specialism_run_by, "specialism", "Dementia", "Independent")
swl_ind = look_up(icb_run_by, "icb", "South West London", "Independent")
swl_nhs = look_up(icb_run_by, "icb", "South West London", "NHS")
westminster_ind = look_up(borough_run_by, "borough", "Westminster", "Independent")
westminster_nhs = look_up(borough_run_by, "borough", "Westminster", "NHS")
camden_ind = look_up(borough_run_by, "borough", "Camden", "Independent")
camden_nhs = look_up(borough_run_by, "borough", "Camden", "NHS")


# ---------- styling ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@700;800&display=swap');
    h1, h2, h3, .title, .section, .ban-number {font-family: 'Fira Sans', sans-serif !important;}
    .block-container {max-width: 1250px; padding-top: 2rem;}

    /* header */
    .header {display: flex; align-items: center; justify-content: center; gap: 24px; margin-bottom: 1.2rem;}
    .title {font-size: 2.6rem; font-weight: 800; line-height: 1.25; text-align: center; color: #1E1B26;}
    .title small {display: block; font-size: 1.7rem; margin-top: 4px;}
    .tagline {text-align: center; color: #5B2A86; font-weight: 700; font-size: 1.15rem; margin-bottom: 1rem;}
    .intro {background: #EFE9F5; border-left: 6px solid #5B2A86; border-radius: 10px;
            padding: 16px 24px; font-size: 1.05rem; line-height: 1.7; margin-bottom: 1rem;}
    .nhs {color: #5B2A86; font-weight: 700;}
    .ind {color: #C2185B; font-weight: 700;}
    .gap {color: #B37400; font-weight: 700;}

    /* the big numbers (BANs) */
    .bans {display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 0.8rem;}
    .ban {background: #F5F4F8; border-radius: 14px; padding: 18px; text-align: center;}
    .ban-label {font-weight: 700; font-size: 1rem;}
    .ban-number {font-size: 2.8rem; font-weight: 800; line-height: 1.2;}
    .ban-note {color: #5A5666; font-size: 0.92rem;}

    .key {text-align: center; margin: 0.4rem 0 0.2rem 0;}
    .dot {display: inline-block; width: 13px; height: 13px; border-radius: 50%; margin: 0 6px 0 18px; vertical-align: -1px;}

    /* section titles: centred, black bar on the left, optional info icon */
    .section {text-align: center; font-size: 1.8rem; font-weight: 800; margin: 3rem 0 0.2rem 0; color: #1E1B26;}
    .section span.bar {border-left: 8px solid #1E1B26; padding-left: 14px;}
    .section-sub {text-align: center; color: #5A5666; font-size: 1.02rem; margin: 0 0 1rem 0;}
    .info {position: relative; display: inline-block; width: 22px; height: 22px; border: 2px solid #1E1B26; border-radius: 50%;
           font-size: 0.85rem; line-height: 18px; text-align: center; margin-left: 10px; cursor: help;
           vertical-align: middle; font-family: Georgia, serif; font-weight: 700;}
    .info .tip {visibility: hidden; position: absolute; z-index: 10; top: 30px; left: 50%; transform: translateX(-50%);
                width: 340px; background: #2E2346; color: white; text-align: left; border-radius: 8px;
                padding: 12px 14px; font-family: 'Source Sans Pro', sans-serif; font-size: 0.92rem;
                font-weight: 400; line-height: 1.5;}
    .info:hover .tip {visibility: visible;}

    /* every chart sits in a soft grey card */
    div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"] {
        background: #F5F4F8; border: none !important; border-radius: 16px; padding: 1.2rem 1.4rem;}
    div[data-testid="stLayoutWrapper"] > div.st-key-finder {background: #F4EEF7;}
    .chart-sub {color: #3B3747; margin-top: -0.6rem; line-height: 1.5;}

    /* conclusion and register sections: banner + 3 numbered cards */
    .banner-dark {background: #2E2346; color: white; font-weight: 700; text-align: center;
                  border-radius: 10px; padding: 18px 24px; font-size: 1.1rem; margin-bottom: 1rem; line-height: 1.6;}
    .banner-light {background: #EFE9F5; color: #1E1B26; font-weight: 700; text-align: center;
                   border-radius: 10px; padding: 18px; font-size: 1.05rem; margin-bottom: 1rem;}
    .card {background: #F5F4F8; border-radius: 14px; padding: 18px 22px; height: 100%; line-height: 1.65; font-size: 1.02rem;}
    .card b.head {display: block; font-size: 1.08rem; margin-bottom: 4px;}
    .about {color: #5A5666; font-size: 0.95rem; line-height: 1.7;}
    </style>
    """,
    unsafe_allow_html=True,
)


def section(title, subtitle="", info=""):
    # centred heading with a black bar; hover the (i) for extra detail
    icon = f'<span class="info">i<span class="tip">{info}</span></span>' if info else ""
    st.markdown(f'<div class="section"><span class="bar">{title}</span>{icon}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)


def chart_title(title, finding):
    # the subtitle states the finding, not just what the chart is
    st.markdown(f"### {title}")
    st.markdown(f'<p class="chart-sub">{finding}</p>', unsafe_allow_html=True)


def colour_key():
    st.markdown(
        f'<div class="key"><b>Colour key:</b>'
        f'<span class="dot" style="background:{PURPLE}"></span><b>NHS</b>'
        f'<span class="dot" style="background:{PINK}"></span><b>Independent provider</b>'
        f'<span class="dot" style="background:{COLOURS["Other"]}"></span><b>Other (e.g. social care)</b>'
        f'<span class="dot" style="background:{AMBER}"></span><b>None registered locally</b></div>',
        unsafe_allow_html=True,
    )


def cards(items):
    for col, (head, text) in zip(st.columns(len(items)), items):
        col.markdown(f"<div class='card'><b class='head'>{head}</b>{text}</div>", unsafe_allow_html=True)


def tidy(chart):
    # same fonts and no outline on every chart
    return (
        chart.configure_axis(labelFontSize=13, titleFontSize=14, labelColor="#3B3747", titleColor="#5A5666")
        .configure_view(strokeWidth=0)
    )


# stacked bars coloured by who runs the service.
# the "services" column already holds the count from the mart, the chart only draws it.
# share=True draws each bar as 100% so the split is easy to compare. Biggest bars first.
def run_by_bars(data, field, label, share, horizontal=True, height=400):
    colour = alt.Color(
        "run_by:N", scale=alt.Scale(domain=list(COLOURS), range=list(COLOURS.values())), legend=None
    )
    biggest_first = alt.EncodingSortField(field="services", op="sum", order="descending")
    value = alt.X(
        "services:Q",
        title="Share of services" if share else "Services",
        stack="normalize" if share else True,
        axis=alt.Axis(format="%" if share else "d"),
    )
    if horizontal:
        x = value
        y = alt.Y(f"{field}:N", title=None, sort=biggest_first, axis=alt.Axis(labelLimit=220))
    else:
        x = alt.X(f"{field}:N", title=None, sort=biggest_first, axis=alt.Axis(labelAngle=-90, labelLimit=200))
        y = alt.Y("services:Q", title="Services")
    tooltip = [
        alt.Tooltip(f"{field}:N", title=label),
        alt.Tooltip("run_by:N", title="Run by"),
        alt.Tooltip("services:Q", title="Services"),
    ]
    chart = alt.Chart(data).mark_bar().encode(
        x=x, y=y, color=colour, order=alt.Order("stack:Q"), tooltip=tooltip
    )
    return tidy(chart.properties(height=height))


# ---------- header ----------
heart_icon = """
<svg width="90" height="90" viewBox="0 0 90 90">
  <rect width="90" height="90" rx="18" fill="#5B2A86"/>
  <path d="M45 70 C20 52 16 40 22 31 C28 22 40 23 45 32 C50 23 62 22 68 31 C74 40 70 52 45 70 Z" fill="white"/>
  <path d="M30 44 H39 L42 37 L47 52 L51 41 H60" stroke="#C2185B" stroke-width="3.5" fill="none"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""
st.markdown(
    f'<div class="header">{heart_icon}<div class="title">London\'s Mental Health Services'
    '<small>Who Provides Care, and Where Is <span style="color:#D98E04">More Support</span> Needed?</small></div></div>'
    '<div class="tagline">Built for service planners in London, and for anyone looking for a registered mental health service</div>'
    '<div class="intro">London commissions mental health care from both the <span class="nhs">NHS</span> and '
    '<span class="ind">independent</span> providers. Using the CQC register, this dashboard looks at '
    "<b>who provides</b> each kind of service, <b>where</b> services are, and <b>where more support may be "
    "needed</b>. You can then <b>look up services</b> yourself, and see what the register can't show.</div>",
    unsafe_allow_html=True,
)

# reads: mart_summary and mart_gaps_summary
st.markdown(
    f"""
<div class="bans">
  <div class="ban"><div class="ban-label" style="color:{PURPLE}">Registered services</div>
    <div class="ban-number" style="color:{PURPLE}">{int(summary["services"])}</div>
    <div class="ban-note">mental health sites in London</div></div>
  <div class="ban"><div class="ban-label" style="color:{PINK}">Independent providers</div>
    <div class="ban-number" style="color:{PINK}">{pct_independent}%</div>
    <div class="ban-note">of sites: {independent} independent vs {nhs} NHS</div></div>
  <div class="ban"><div class="ban-label" style="color:{PURPLE}">Boroughs with a service</div>
    <div class="ban-number" style="color:{PURPLE}">{int(summary["boroughs_with_service"])} of 33</div>
    <div class="ban-note">London's 32 boroughs plus the City</div></div>
  <div class="ban"><div class="ban-label" style="color:{AMBER}">No eating disorder service</div>
    <div class="ban-number" style="color:{AMBER}">{no_eating} of 33</div>
    <div class="ban-note">boroughs with none registered locally</div></div>
</div>
""",
    unsafe_allow_html=True,
)
colour_key()


# ---------- who provides them ----------
section(
    "Who Provides London's Mental Health Services?",
    "The NHS and independent providers split the work very differently depending on the need.",
    info="NHS = run by an NHS trust. Independent = a private or charity healthcare provider. "
         "Other = e.g. social care or a local authority. Taken from the CQC provider type. "
         "Counts are registered sites, not beds or capacity.",
)

c1, c2 = st.columns(2)
with c1.container(border=True):
    # reads: mart_specialism_run_by
    chart_title(
        "Who provides each type of service?",
        f'<span class="ind">Substance misuse</span> is mostly independent ({substance_ind} vs {substance_nhs} NHS), '
        f'while <span class="nhs">dementia</span> is almost all NHS ({dementia_nhs} NHS, {dementia_ind} independent).',
    )
    st.altair_chart(run_by_bars(specialism_run_by, "specialism", "Type of service", share=True, height=420),
                    width="stretch")
with c2.container(border=True):
    # reads: mart_icb_run_by
    chart_title(
        "Does it differ across London's ICBs?",
        f'<b>South West London</b> leans most on <span class="ind">independent</span> providers: '
        f"{swl_ind} independent vs {swl_nhs} NHS sites.",
    )
    st.altair_chart(run_by_bars(icb_run_by, "icb", "ICB", share=True, height=420), width="stretch")


# ---------- where they are ----------
section(
    "Where Are the Services?",
    "Services cluster in central London, and who provides them changes from borough to borough.",
    info="Counts where a site is registered, not where its patients live. "
         "Raw counts, not adjusted for borough population. Boroughs with no services don't appear.",
)
with st.container(border=True):
    # reads: mart_borough_run_by
    chart_title(
        "Which boroughs have the most services?",
        f'<b>Westminster</b> has the most, and most are <span class="ind">independent</span> '
        f'({westminster_ind} vs {westminster_nhs} NHS). <b>Camden\'s</b> are almost all '
        f'<span class="nhs">NHS</span> ({camden_nhs} vs {camden_ind} independent).',
    )
    st.altair_chart(run_by_bars(borough_run_by, "borough", "Borough", share=False, horizontal=False, height=400),
                    width="stretch")


# ---------- where more support is needed ----------
section(
    "Where Is More Support Needed?",
    'Boroughs with <span class="gap">no service of a given type registered locally</span>.',
    info="This shows supply only: where services are registered. Judging need would also take demand (population and how common each condition is), which is the next step. "
         "None registered locally is not the same as no access: people may be served from a neighbouring borough. "
         "NHS community mental health teams are often registered under their trust's head office, "
         "so a borough can look emptier than it is. A service with several specialisms counts in each.",
)


def colour_cell(value):
    # amber for 0 (none registered), darker purple for more services
    if value == 0:
        return "background-color: #FFF1D6; color: #B37400; font-weight: 700"
    strength = min(value, 8) / 10
    text = "white" if value >= 6 else "#1E1B26"
    return f"background-color: rgba(91, 42, 134, {strength}); color: {text}"


# mart_gaps is one row per borough and specialism. pivot only turns it sideways into a grid
# (boroughs down the side, one column per specialism). No numbers change.
grid = gaps.pivot(index="borough", columns="specialism", values="services")
grid = grid[none_per_need.sort_values(ascending=False).index]  # biggest gaps first
grid.index.name = "Borough"

# stacked (not side by side), so the chart and the grid both get the full width
with st.container(border=True):
    # reads: mart_gaps_summary
    chart_title(
        "Which needs have no local service in the most boroughs?",
        f'<span class="gap">Eating disorders</span>: {no_eating} of 33 boroughs have none, more than any '
        f'other mental health need. <span class="gap">Children and young people</span>: {no_children}.',
    )
    bars = alt.Chart(gaps_summary).encode(
        x=alt.X("boroughs_with_none:Q", title="Boroughs with none", scale=alt.Scale(domain=[0, 33])),
        y=alt.Y("specialism:N", sort="-x", title=None, axis=alt.Axis(labelLimit=200)),
        tooltip=[alt.Tooltip("specialism:N", title="Type of service"),
                 alt.Tooltip("boroughs_with_none:Q", title="Boroughs with none")],
    )
    gap_chart = (
        bars.mark_bar().encode(
            color=alt.condition("datum.highlight", alt.value(AMBER), alt.value(MUTED))
        )
        + bars.mark_text(align="left", dx=4, fontSize=12, color="#3B3747").encode(text="boroughs_with_none:Q")
    )
    st.altair_chart(tidy(gap_chart.properties(height=380)), width="stretch")
with st.container(border=True):
    # reads: mart_gaps
    chart_title(
        "Borough by borough: services of each type",
        'Registered services per borough and type. <span class="gap">0 = none registered locally</span>. '
        '<span class="nhs">Darker purple = more services</span>.',
    )
    st.dataframe(grid.style.map(colour_cell), height=480, width="stretch")


# ---------- find a service ----------
# reads: mart_services (the app only filters it, nothing is counted)
section(
    "Look Up a Service",
    "Explore the register yourself: filter by borough, by who it's for, and by who provides it.",
    info="Pick more than one type to see services that cover any of them. "
         "Hover a dot on the map for its name.",
)


def reset_filters():
    st.session_state["borough"] = "All of London"
    st.session_state["needs"] = []
    del st.session_state["run_by"]  # goes back to its default, "All"


with st.container(border=True, key="finder"):
    f1, f2, f3 = st.columns([3, 3, 2])
    borough = f1.selectbox("Borough", ["All of London"] + sorted(services["borough"].unique()), key="borough")
    needs = f2.multiselect("Type of service / who it's for", list(SHORT.values()),
                           placeholder="Any type", key="needs")
    run_by = f3.segmented_control("Run by", ["All", "NHS", "Independent"], default="All", key="run_by")

    found = services
    if borough != "All of London":
        found = found[found["borough"] == borough]
    if needs:
        # a service matches if its specialisms include ANY of the chosen ones
        full_names = [name for name, short in SHORT.items() if short in needs]
        found = found[found["specialisms"].fillna("").apply(lambda s: any(n in s for n in full_names))]
    if run_by and run_by != "All":
        found = found[found["run_by"] == run_by]

    c1, c2 = st.columns([5, 1])
    status = "no filters applied" if len(found) == len(services) else "filtered"
    c1.markdown(f"#### {len(found)} services · {status}")
    c2.button("Reset filters", icon=":material/refresh:", on_click=reset_filters, width="stretch")

    map_col, table_col = st.columns([3, 2])
    map_col.map(found, latitude="latitude", longitude="longitude", color="colour", size=120, zoom=9, height=520)
    table_col.dataframe(
        found[["name", "borough", "run_by", "specialisms"]].sort_values("name"),
        column_config={"name": "Service", "borough": "Borough", "run_by": "Run by", "specialisms": "Who it's for"},
        hide_index=True,
        height=520,
        width="stretch",
    )


# ---------- what the register can't show ----------
section(
    "What Can't the Register Show?",
    info="CQC registers organisations that carry out a regulated activity: treatment, personal care, "
         "or accommodation with nursing or personal care. Anything else isn't in the register.",
)
st.markdown(
    "<div class='banner-light'>Much of what frontline practitioners signpost people to isn't a CQC-registered "
    "mental health service, so it can't appear here.</div>",
    unsafe_allow_html=True,
)
cards([
    ("1 · Hidden inside other records",
     "NHS community teams and some crisis houses are registered under their trust, not as their own sites."),
    ("2 · Registered, but not as mental health",
     "Some private clinics offering mental health care (e.g. ADHD assessment) are registered as GP or "
     "doctors' services, so a mental health filter misses them."),
    ("3 · Not in the register at all",
     "Charities and community groups (peer support, advocacy, refugee and women's groups), hostels and "
     "supported housing, English classes (ESOL) and helplines such as Samaritans."),
])


# ---------- about the data ----------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f"""
<div class="about">
<b>Source:</b> Care Quality Commission (CQC) public API, pulled on {SNAPSHOT}: registered care locations in
England, filtered to London locations with a mental health or substance misuse service type, and currently
registered.<br>
<b>One row:</b> one registered CQC location (a site), identified by its CQC location ID. &nbsp;
<b>ICB:</b> Integrated Care Board, the NHS body that plans and funds health services for an area.<br>
<b>Limitations:</b> a snapshot (CQC overwrites provider history, so no change over time); counts are sites,
not beds or capacity; not adjusted for population.<br><br>
<b>Created by Vasana Attanayake</b>
</div>
""",
    unsafe_allow_html=True,
)
