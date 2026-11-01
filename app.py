from flask import Flask, render_template, request, redirect, url_for
from database import create_table, get_db_connection
from datetime import date
app = Flask(__name__)

create_table()


# Dashboard
@app.route("/")
def dashboard():

    conn = get_db_connection()

    total_leads = conn.execute(
        "SELECT COUNT(*) FROM leads"
    ).fetchone()[0]

    new_leads = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = 'New'"
    ).fetchone()[0]

    interested_leads = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = 'Interested'"
    ).fetchone()[0]

    converted_leads = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = 'Converted'"
    ).fetchone()[0]

    lost_leads = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = 'Lost'"
    ).fetchone()[0]

    contacted_leads = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = 'Contacted'"
    ).fetchone()[0]

    recent_leads = conn.execute(
        "SELECT * FROM leads ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_leads=total_leads,
        new_leads=new_leads,
        interested_leads=interested_leads,
        converted_leads=converted_leads,
        contacted_leads=contacted_leads,
        lost_leads=lost_leads,
        recent_leads=recent_leads
    )


# VIEW ALL LEADS WITH SEARCH AND FILTERS
@app.route("/leads")
def leads():

    search = request.args.get("search", "").strip()
    selected_status = request.args.get("status", "")
    selected_source = request.args.get("source", "")

    conn = get_db_connection()

    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    # Search by name, email, phone or company
    if search:
        query += """
            AND (
                name LIKE ?
                OR email LIKE ?
                OR phone LIKE ?
                OR company LIKE ?
            )
        """

        search_term = f"%{search}%"
        params.extend([search_term] * 4)

    # Filter by status
    if selected_status:
        query += " AND status = ?"
        params.append(selected_status)

    # Filter by source
    if selected_source:
        query += " AND source = ?"
        params.append(selected_source)

    query += " ORDER BY created_at DESC"

    all_leads = conn.execute(query, params).fetchall()

    # Get available lead sources for the dropdown
    sources = conn.execute("""
        SELECT DISTINCT source
        FROM leads
        WHERE source IS NOT NULL AND source != ''
        ORDER BY source
    """).fetchall()

    conn.close()

    return render_template(
        "leads.html",
        leads=all_leads,
        search=search,
        selected_status=selected_status,
        selected_source=selected_source,
        sources=sources
    )


# ADD NEW LEAD
@app.route("/add-lead", methods=["GET", "POST"])
def add_lead():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        company = request.form.get("company", "").strip()
        source = request.form.get("source", "").strip()
        status = request.form.get("status", "New")
        follow_up_date = request.form.get("follow_up_date", "")
        notes = request.form.get("notes", "").strip()

        if not name:
            return render_template(
                "add_lead.html",
                error="Customer name is required."
            )

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO leads
            (name, email, phone, company, source, status,
             follow_up_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email, phone, company, source, status,
            follow_up_date, notes
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("leads"))

    return render_template("add_lead.html")


# EDIT LEAD
@app.route("/edit-lead/<int:lead_id>", methods=["GET", "POST"])
def edit_lead(lead_id):

    conn = get_db_connection()

    lead = conn.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    if lead is None:
        conn.close()
        return "Lead not found", 404

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        company = request.form.get("company", "").strip()
        source = request.form.get("source", "").strip()
        status = request.form.get("status", "New")
        follow_up_date = request.form.get("follow_up_date", "")
        notes = request.form.get("notes", "").strip()

        if not name:
            conn.close()
            return render_template(
                "edit_lead.html",
                lead=lead,
                error="Customer name is required."
            )

        conn.execute("""
            UPDATE leads
            SET name = ?,
                email = ?,
                phone = ?,
                company = ?,
                source = ?,
                status = ?,
                follow_up_date = ?,
                notes = ?
            WHERE id = ?
        """, (
            name, email, phone, company, source, status,
            follow_up_date, notes, lead_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("leads"))

    conn.close()

    return render_template("edit_lead.html", lead=lead)


# DELETE LEAD
@app.route("/delete-lead/<int:lead_id>", methods=["POST"])
def delete_lead(lead_id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM leads WHERE id = ?",
        (lead_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("leads"))

# FOLLOW-UP MANAGER
@app.route("/follow-ups")
def follow_ups():

    today = date.today().isoformat()

    conn = get_db_connection()

    todays_follow_ups = conn.execute("""
        SELECT * FROM leads
        WHERE follow_up_date = ?
        AND status NOT IN ('Converted', 'Lost')
        ORDER BY name
    """, (today,)).fetchall()

    upcoming_follow_ups = conn.execute("""
        SELECT * FROM leads
        WHERE follow_up_date > ?
        AND status NOT IN ('Converted', 'Lost')
        ORDER BY follow_up_date
    """, (today,)).fetchall()

    overdue_follow_ups = conn.execute("""
        SELECT * FROM leads
        WHERE follow_up_date < ?
        AND follow_up_date != ''
        AND status NOT IN ('Converted', 'Lost')
        ORDER BY follow_up_date
    """, (today,)).fetchall()

    conn.close()

    return render_template(
        "follow_ups.html",
        todays_follow_ups=todays_follow_ups,
        upcoming_follow_ups=upcoming_follow_ups,
        overdue_follow_ups=overdue_follow_ups
    )
if __name__ == "__main__":
    app.run(debug=True)