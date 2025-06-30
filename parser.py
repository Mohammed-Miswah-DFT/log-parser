import re
import sys
from collections import defaultdict
from jinja2 import Template

def extract_exceptions(log_text):
    pattern = re.compile(
        r'CRIT\|.*?\|(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)\|.*?\|\|(?P<message>.*?)(?=\n\S|\Z)',
        re.DOTALL
    )
    grouped = defaultdict(list)

    for match in pattern.finditer(log_text):
        timestamp = match.group("timestamp")
        message = match.group("message").strip()

        exception_type_match = re.search(r'(\w+\.)*(\w+Exception)\b', message)
        exception_type = exception_type_match.group(2) if exception_type_match else "UnknownException"

        grouped[exception_type].append({
            "timestamp": timestamp,
            "message": message
        })

    return grouped

def render_html_report(grouped_exceptions, output_file):
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Parsed Log Report</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; }
            pre { white-space: pre-wrap; word-wrap: break-word; }
            .filters { margin-bottom: 20px; }
            .accordion-button::after { margin-left: auto; }
        </style>
    </head>
    <body>
        <h2>Grouped Exception Report</h2>
        <div class="filters row g-2">
            <div class="col-md-4">
                <input type="text" id="searchBox" class="form-control" placeholder="Search exception type...">
            </div>
            <div class="col-md-2">
                <input type="date" id="fromDate" class="form-control" />
            </div>
            <div class="col-md-2">
                <input type="date" id="toDate" class="form-control" />
            </div>
            <div class="col-md-2">
                <button id="resetBtn" class="btn btn-secondary w-100">Reset Filters</button>
            </div>
        </div>

        <p id="totalGroups">Total Groups: {{ grouped|length }}</p>

   <div class="accordion" id="exceptionAccordion">
    {% for exception_type, entries in grouped.items() %}
    <div class="accordion-item mb-3 exception-group" data-type="{{ exception_type }}">
        <h2 class="accordion-header" id="heading{{ loop.index }}">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                data-bs-target="#collapse{{ loop.index }}">
                <span class="group-title">{{ exception_type }}</span>
                (<span class="occ-count">{{ entries|length }}</span> &nbsp occurrences)
            </button>
        </h2>
        <div id="collapse{{ loop.index }}" class="accordion-collapse collapse">
            <div class="accordion-body">
                <div class="accordion" id="exceptionInsideAccordion">
                    {% for entry in entries %}
                  {% set short_type = entry.message.split(':')[0] %}
                    <div class="accordion-item mb-3 exception-group" data-type="{{ short_type }}">
                        <h2 class="accordion-header" id="heading{{ loop.index }}">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                                data-bs-target="#collapseinside{{ loop.index }}">
                                <span class="group-title">{{ short_type }}</span>
                            </button>
                        </h2>
                        <div id="collapseinside{{loop.index}}" class="accordion-collapse collapse">
                            <div class="accordion-body">
                                <div class="entry" data-date="{{ entry.timestamp[:10] }}">
                                    <strong>{{ entry.timestamp }}</strong>
                                    <pre>{{ entry.message }}</pre>
                                    <hr>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>

            </div>
        </div>
    </div>
    {% endfor %}
</div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function updateDisplay() {
                const searchTerm = document.getElementById("searchBox").value.toLowerCase();
                const fromDate = document.getElementById("fromDate").value;
                const toDate = document.getElementById("toDate").value;

                let totalGroups = 0;

                document.querySelectorAll(".exception-group").forEach(group => {
                    const type = group.getAttribute("data-type").toLowerCase();
                    const matchesSearch = type.includes(searchTerm);

                    const entries = group.querySelectorAll(".entry");
                    let visibleCount = 0;

                    entries.forEach(entry => {
                        const entryDate = entry.getAttribute("data-date");

                        const show = (!fromDate || entryDate >= fromDate) &&
                                     (!toDate   || entryDate <= toDate);

                        entry.style.display = show ? "" : "none";
                        if (show) visibleCount++;
                    });

                    group.querySelector(".occ-count").textContent = visibleCount;

                    if (matchesSearch && visibleCount > 0) {
                        group.style.display = "";
                        totalGroups++;
                    } else {
                        group.style.display = "none";
                    }
                });

                document.getElementById("totalGroups").textContent = `Total Groups: ${totalGroups}`;
            }

            document.getElementById("searchBox").addEventListener("input", updateDisplay);
            document.getElementById("fromDate").addEventListener("change", updateDisplay);
            document.getElementById("toDate").addEventListener("change", updateDisplay);
            document.getElementById("resetBtn").addEventListener("click", () => {
                document.getElementById("searchBox").value = "";
                document.getElementById("fromDate").value = "";
                document.getElementById("toDate").value = "";
                updateDisplay();
            });

            updateDisplay(); // initial state
        </script>
    </body>
    </html>
    """
    from jinja2 import Template
    template = Template(template_str)
    html = template.render(grouped=grouped_exceptions)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Grouped HTML report generated: {output_file}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python log_exception_report.py <logfile>")
        return

    log_file = sys.argv[1]

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_text = f.read()
    except FileNotFoundError:
        print(f"Error: File '{log_file}' not found.")
        return

    grouped_exceptions = extract_exceptions(log_text)
    render_html_report(grouped_exceptions, "exception_report.html")


if __name__ == "__main__":
    main()
