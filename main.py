from fastapi import FastAPI, UploadFile, File, HTTPException
from bs4 import BeautifulSoup
import re

app = FastAPI(
    title="Course Registration API",
    description="API for importing and retrieving course catalog information",
    version="1.0.0",
)

courses = {}


def extract_course_codes(text: str) -> list[str]:
    pattern = r"\b[A-Za-z]{2,10}\s*\d{4}\b"

    matches = re.findall(pattern, text)

    result = []

    for match in matches:
        letters = re.match(r"[A-Za-z]+", match).group()
        number = re.search(r"\d{4}", match).group()

        course_code = f"{letters.upper()} {number}"

        if course_code not in result:
            result.append(course_code)

    return result


@app.post("/api/v1/admin/catalog/import")
async def import_catalog(file: UploadFile = File(...)):
    html_content = await file.read()

    if not html_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")

    if table is None:
        raise HTTPException(
            status_code=400,
            detail="No course table found in the uploaded HTML file",
        )

    rows = table.find_all("tr")

    if len(rows) < 2:
        raise HTTPException(
            status_code=400,
            detail="Course table contains no course rows",
        )

    imported_count = 0

    for row in rows[1:]:
        cells = row.find_all(["td", "th"])

        if len(cells) < 5:
            continue

        course_code = cells[0].get_text(" ", strip=True)
        title = cells[1].get_text(" ", strip=True)
        credits = cells[2].get_text(" ", strip=True)
        prerequisites_text = cells[3].get_text(" ", strip=True)
        cross_listed_text = cells[4].get_text(" ", strip=True)

        normalized_code = re.sub(r"\s+", "", course_code).upper()

        if not normalized_code:
            continue

        prerequisites = extract_course_codes(prerequisites_text)
        cross_listed = extract_course_codes(cross_listed_text)

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
    normalized_code = re.sub(r"\s+", "", course_code).upper()

    course = courses.get(normalized_code)

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    return course
