import re
import sys
from collections import defaultdict
from jinja2 import Template

def extract_exceptions(log_text):
    pattern = re.compile(
        r'(?P<level>CRIT)\|(?P<app>.*?)\|(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)\|.*?\|\|(?P<message>.*?)(?=\n\S|\Z)',
        re.DOTALL
    )
    matches = pattern.finditer(log_text)
    exceptions = []

    for match in matches:
        full_msg = match.group("message").strip()
        root_line = full_msg.splitlines()[0] if full_msg else "Unknown Exception"
        exceptions.append({
            "timestamp": match.group("timestamp"),
            "full_message": full_msg,
            "root_message": root_line.strip()
        })
    return exceptions

def group_exceptions(exceptions):
    grouped = defaultdict(list)
    for ex in exceptions:
        grouped[ex["root_message"]].append(ex)
    return grouped

def render_html_report(grouped_exceptions, output_file):
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Grouped Exception Report</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .group { border: 1px solid #ddd; margin-bottom: 15px; border-radius: 5px; }
            .group-header { background-color: #f2f2f2; padding: 10px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
            .details { display: none; padding: 10px; background: #fafafa; }
            .timestamp { color: gray; font-size: 0.9em; }
            pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; }
        </style>
        <script>
            function toggleDetails(id) {
                var el = document.getElementById(id);
                el.style.display = el.style.display === 'none' ? 'block' : 'none';
            }
        </script>
    </head>
    <body>
        <h2>Grouped Exception Report</h2>
        <p>Total Exception Groups: {{ grouped_exceptions|length }}</p>

        {% for root, group in grouped_exceptions.items() %}
        <div class="group">
            <div class="group-header" onclick="toggleDetails('group{{ loop.index }}')">
                <strong>{{ root }}</strong>
                <span>{{ group|length }} occurrence(s)</span>
            </div>
            <div class="details" id="group{{ loop.index }}">
                {% for ex in group %}
                <p class="timestamp">{{ ex.timestamp }}</p>
                <pre>{{ ex.full_message }}</pre>
                <hr>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </body>
    </html>
    """
    template = Template(template_str)
    html = template.render(grouped_exceptions=grouped_exceptions)

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

    exceptions = extract_exceptions(log_text)
    grouped = group_exceptions(exceptions)
    render_html_report(grouped, "grouped_exception_report.html")

if __name__ == "__main__":
    main()
