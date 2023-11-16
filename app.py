import os 
from flask import Flask, request,render_template
import psycopg2
from psycopg2.extras import RealDictCursor



conn = psycopg2.connect(
    "postgres://legos_user:C5zVYNrlLNN1QTZcnLR9JqncahDpRpKg@dpg-cla17u62eqrc7394na0g-a/legos",
    cursor_factory=RealDictCursor)
app = Flask(__name__, template_folder= '')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)




SORT_COLUMNS ={"set_name", "year", "theme_name", "part_count"}
SORT_ORDER ={"asc","desc"}
LIMIT ={10,50,100}


def parse_int_list(value, valid_values, default_value):
    try:
        int_value = value
        for v in valid_values:
            if v == int_value:
                return v
        return default_value
    except:
        return default_value
def parse_int_list2(value, valid_values, default_value):
    try:
        int_value = int(value)
        for v in valid_values:
            if v == int_value:
                return v
        return default_value
    except:
        return default_value
def check_part(value, default_value):
    try:
        part_count_gte = int(value)
        if part_count_gte < 0:
            return default_value
        return part_count_gte
    except:
        return default_value
    

    
@app.route("/")
def hello_world():
    name = request.args.get("name", "World")
    return f"<p>Hello, {name}!</p>"

@app.route("/sets", methods= ['GET', 'POST'])
def render_sets():
    if request.method == 'POST':
        set_name = request.form["set_name"]
        set_num2 = request.form["set_num2"]
        star = request.form["star"]
        sort_by = 'set_name'
        sort_dir = 'asc'
        limit = 500
        part_count_gte = 0
        part_count_lte = 100000
        page_num = 1
        theme_name = ""
        search_by = 'true,false'
    else:
        set_name = request.args.get("set_name", "")
        set_num2 = request.args.get("set_num2", "")
        theme_name = request.args.get("theme_name", "")
        limit = parse_int_list2(request.args.get("limit", 50, type= int),{10,20,50}, 50)
        part_count_gte = check_part(request.args.get("part_count_gte", 0, type=int),0)
        part_count_lte = check_part(request.args.get("part_count_lte", 100000, type=int),100000)
        sort_by = parse_int_list(request.args.get("sort_by", "set_name"),{"set_name", "year", "theme_name", "part_count"},"set_name")
        sort_dir = parse_int_list(request.args.get("sort_dir","asc"),{"asc","desc"}, "asc")
        page_num = check_part(request.args.get("page_num",1, type=int),1)
        star = request.args.get("star",False, type=bool)
        search_by = request.args.get("search_by","true,false")

        if sort_dir not in SORT_ORDER:
            sort_dir = "asc"
        if sort_by not in SORT_COLUMNS:
            sort_by = "set_name"
        
    if star == 'true':
        star = True
    else:
        star = False  
    if search_by not in ['true','false','true,false']:
        search_by = 'true,false'

    with conn.cursor() as cur:
        cur.execute("update set set starred = %(star)s where set_num = %(set_num2)s ", {
                        "star" : star,
                        "set_num2": set_num2})
        conn.commit()
        
        
    from_where_clause =f"""
    from set s
    inner join theme t on s.theme_id = t.id
    inner join inventory i on s.set_num = i.set_num
    inner join inventory_part ip on ip.inventory_id = i.id 
    where s.name ilike %(set_name)s
        and t.name ilike %(theme_name)s and s.starred IN ({search_by})
     group by s.name,s.year,t.name,s.set_num
     having Count(s.num_parts) >= %(part_count_gte)s and Count(s.num_parts) <= %(part_count_lte)s
     order by {sort_by} {sort_dir}
     limit 500
     """
    

    params = {
        "set_name": f"%{set_name}%",
        "theme_name": f"%{theme_name}%",
        "limit": limit,
        "part_count_gte": part_count_gte,
        "part_count_lte": part_count_lte,
        "offset" : (page_num-1)*limit,
        "star" : star
    }
    params1 ={
        "star" : star,
        "set_num2": f"%{set_num2}%"
    }
    def get_sort_dir(col):
        if col == sort_by:
            if sort_dir == "asc":
                return "desc"
            else:
                return "asc" 
        else:
            return "asc"
    def get_page_num(name):
        if name != 1:
            return page_num
        else:
            return 1
        
    try:
        with conn.cursor() as cur:
            cur.execute(f"""select s.name as set_name,Count(s.num_parts) as part_count, s.year,t.name as theme_name, s.set_num as set_num, s.starred as star
                            {from_where_clause}""",
                        params)
            results = list(cur.fetchall())

            cur.execute("""select count(*) from 
                        (select s.name as set_name 
                        from set s 
                        inner join theme t on s.theme_id = t.id
                        inner join inventory i on s.set_num = i.set_num
                        inner join inventory_part ip on ip.inventory_id = i.id 
                        where s.name ilike %(set_name)s
                            and t.name ilike %(theme_name)s
                        group by s.name,s.year,t.name,s.set_num
                        having Count(s.num_parts) >= %(part_count_gte)s and Count(s.num_parts) <= %(part_count_lte)s) as count""",
                        params)
            count = cur.fetchone()["count"]
    except Exception as e:
        # Rollback the transaction
        conn.rollback()
        print(f"Error: {e}")

    

        # cur.execute("update set set starred = %(star)s where name ilike %(set_num2)s", params1)
        # conn.commit()
        
    

        return render_template("sets.html",
                               params=request.args,
                               result_count_r=count,
                               sets=results,
                               per_page = limit,
                               get_sort_dir=get_sort_dir,
                               get_page_num=get_page_num,
                               search_by=search_by,
                               starred = star
                                )
    

@app.route("/my-sets", methods=['GET','POST'])
def render_my_sets():
    if request.method == 'POST':
        set_num2 = request.form["set_num2"]
    else:        
        set_num2 = request.args.get("set_num2","")
    
   
    value= True

    with conn.cursor() as cur:
        cur.execute("update set set starred = false where set_num = %(set_num2)s ", {
                        "set_num2": set_num2})
        conn.commit()     
        
    from_where_clause ="""
    from set s
    inner join theme t on s.theme_id = t.id
    inner join inventory i on s.set_num = i.set_num
    inner join inventory_part ip on ip.inventory_id = i.id 
    where s.starred is true 
     group by s.name,s.year,t.name,s.set_num
     order by s.name
     limit 500
    """
    

    

    with conn.cursor() as cur:
        cur.execute(f"""select s.name as set_name,s.num_parts as part_count, s.year,t.name as theme_name, s.set_num as set_num, s.starred as star
                        {from_where_clause}""")
        results = list(cur.fetchall())


        cur.execute("""select count(*) from 
                    (select s.name as set_name 
                    from set s 
    inner join theme t on s.theme_id = t.id
    inner join inventory i on s.set_num = i.set_num
    inner join inventory_part ip on ip.inventory_id = i.id 
    where s.starred is true
     group by s.name,s.year,t.name,s.set_num
     ) as count""")
        result_count_r = cur.fetchone()["count"]
    

        return render_template("my-sets.html",
                               params=request.args,
                               results=results,
                               Value= value,
                               result_count_r=result_count_r)