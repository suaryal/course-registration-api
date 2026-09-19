from fastapi import FastAPI, UploadFile, File, HTTPException
from bs4 import BeautifulSoup

app = FastAPI(
    title="Course Registration API",
    description="API for importing and retrieving course catalog information",
    version="1.0.0",
)

courses = {}


@app.post("/api/v1/admin/catalog/import")
async def import_catalog(file: UploadFile = File(...)):
    html_content = await file.read()

    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")

    if table is None:
        raise HTTPException(
            status_code=400,
            detail="No course table found in the uploaded HTML file",
        )

    rows = table.find_all("tr")
    imported_count = 0

    for row in rows[1:]:
        cells = row.find_all(["td", "th"])

        if len(cells) < 5:
            continue

        course_code = cells[0].get_text(strip=True)
        title = cells[1].get_text(strip=True)
        credits = cells[2].get_text(strip=True)
        prerequisites = cells[3].get_text(strip=True)
        cross_listed = cells[4].get_text(strip=True)

        normalized_code = course_code.replace(" ", "").upper()

        if not normalized_code:
            continue

        courses[normalized_code] = {
            "course_code": course_code,
            "title": title,
            "credits": credits,
            "prerequisites": prerequisites,
            "cross_listed": cross_listed,
        }

        imported_count += 1

    return {
        "message": "Catalog imported successfully",
        "courses_imported": imported_count,
        "total_courses": len(courses),
    }


@app.get("/api/v1/catalog/courses/{course_code}")
async def get_course(course_code: str):
    normalized_code = course_code.replace(" ", "").upper()

    course = courses.get(normalized_code)

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    return course