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
        <title>Grouped Exception Report</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; }
            pre { white-space: pre-wrap; word-wrap: break-word; }
            .search-input { margin-bottom: 20px; width: 400px; }
            .accordion-button::after { margin-left: auto; }
        </style>
    </head>
    <body>
        <h2>Grouped Exception Report</h2>
        <p>Total Groups: {{ grouped|length }}</p>

        <input type="text" id="searchBox" class="form-control search-input" placeholder="Search exception type...">

        <div class="accordion" id="exceptionAccordion">
        {% for exception_type, entries in grouped.items() %}
            <div class="accordion-item mb-3">
                <h2 class="accordion-header" id="heading{{ loop.index }}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{{ loop.index }}">
                        {{ exception_type }} ({{ entries|length }} occurrences)
                    </button>
                </h2>
                <div id="collapse{{ loop.index }}" class="accordion-collapse collapse">
                    <div class="accordion-body">
                        {% for entry in entries %}
                            <div class="mb-3">
                                <strong>{{ entry.timestamp }}</strong>
                                <pre>{{ entry.message }}</pre>
                                <hr>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        {% endfor %}
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.getElementById("searchBox").addEventListener("keyup", function() {
                const filter = this.value.toLowerCase();
                const items = document.querySelectorAll(".accordion-item");
                items.forEach(item => {
                    const heading = item.querySelector(".accordion-button").innerText.toLowerCase();
                    item.style.display = heading.includes(filter) ? "" : "none";
                });
            });
        </script>
    </body>
    </html>
    """
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
