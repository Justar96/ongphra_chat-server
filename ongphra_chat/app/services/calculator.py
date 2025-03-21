from datetime import datetime

# Determine the Thai zodiac year based on the Gregorian year
def get_thai_zodiac_year_index(year):
    return (year - 4) % 12 + 1

def generate_day_values(starting_value, total_values):
    # Generate the sequence starting from the given value
    values = list(range(1, total_values + 1))
    starting_index = starting_value - 1
    return values[starting_index:] + values[:starting_index]

def get_day_of_week_index(date):
    # Get the day of the week with Sunday as 1
    return (date.weekday() + 1) % 7 + 1

def get_wrapped_index(index, total_values):
    # Wrap the index to ensure it cycles within the total number of values
    return ((index - 1) % total_values) + 1

def calculate_sum_base(base_1, base_2, base_3):
    # Calculate the sum of values from bases 1, 2, and 3 without wrapping
    sum_values = [(base_1[i] + base_2[i] + base_3[i]) for i in range(len(base_1))]
    return sum_values

def generate_data(birth_date_str):
    year, month, day = map(int, birth_date_str.split('-'))

    # Convert to Gregorian year if input is in BE
    if year > 2300:
        year -= 543

    birth_date = datetime(year, month, day)
    day_index = get_day_of_week_index(birth_date)
    month_index = birth_date.month
    year = birth_date.year

    # Row 1: Day of the week
    row_1 = generate_day_values(day_index, 7)

    # Row 2: Month with December as the first month, plus 1
    wrapped_month_index = get_wrapped_index(month_index + 1, 12)
    row_2 = generate_day_values(wrapped_month_index, 7)

    # Row 3: Thai zodiac year
    thai_zodiac_year_index = get_thai_zodiac_year_index(year)
    wrapped_zodiac_year_index = get_wrapped_index(thai_zodiac_year_index, 12)
    row_3 = generate_day_values(wrapped_zodiac_year_index, 7)

    # Row 4: Sum of Row 1, Row 2, and Row 3
    row_4 = calculate_sum_base(row_1, row_2, row_3)

    return row_1, row_2, row_3, row_4

def format_output(row_1, row_2, row_3, row_4):
    day_labels = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
    month_labels = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"]
    year_labels = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]

    base_1 = {label: value for label, value in zip(day_labels, row_1)}
    base_2 = {label: value for label, value in zip(month_labels, row_2)}
    base_3 = {label: value for label, value in zip(year_labels, row_3)}

    return base_1, base_2, base_3, row_4

def seven_nine(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")

    row_1, row_2, row_3, row_4 = generate_data(date_str)
    base_1, base_2, base_3, base_4 = format_output(row_1, row_2, row_3, row_4)
    str_out = ""
    str_out += f"ฐาน 1: {base_1}\n"
    str_out += f"ฐาน 2: {base_2}\n"
    str_out += f"ฐาน 3: {base_3}\n"
    str_out += f"ฐาน 4: {base_4}\n"
    return str_out

print(seven_nine("1998-05-14"))  