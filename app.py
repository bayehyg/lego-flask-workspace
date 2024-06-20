import os 
from flask import Flask, request,render_template,make_response
import psycopg2
from psycopg2.extras import RealDictCursor



conn = psycopg2.connect(
    "postgres://lego_land_db_user:K1rQJJ78QA38zeRuiV2DvNZ8MnWU3mzA@dpg-cppuandds78s73ef0480-a/lego_land_db",
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
    

@app.route("/star")
def update_star():
    star = request.args.get("star", "")
    set_num = request.args.get("set_num", "")
    try:
        print("star ", star, " set_num ", set_num)
        with conn.cursor() as cur:
            cur.execute("UPDATE set SET starred = %(star)s WHERE set_num ILIKE %(set_num2)s", {"star": star, "set_num2": set_num})
            conn.commit()
        return make_response("Success", 200)
    except Exception as e:
        return make_response(str(e), 500)

@app.route("/")
def hello_world():
    name = request.args.get("name", "World")
    return render_template("landing.html")

@app.route("/sets")
def fetch_sets():

    def sanity(value, valid_values, default):
        if(value not in valid_values):
            return default
        else:
            return value
    
    sorts = {'set_num','set_name','theme_name','year','part_count'}
    limits = {10,50,100}
        
    sort_dir = sanity(request.args.get("sort_dir","asc"),{'asc','desc'},'asc')
    set_name = request.args.get("set_name","")
    theme_name = request.args.get("theme_name","")
    min_part_count = request.args.get("min_part_count","0")
    max_part_count = request.args.get("max_part_count","100000")
    limit = sanity(int(request.args.get("limit","50")),limits,50)
    sort_by = sanity(request.args.get("sort_by","set_name"),sorts,'set_name')
    offset = int(request.args.get("offset","0"))
    sort_byp = sanity(request.args.get("sort_byp",""),sorts,'')

    if not isinstance(offset,int):
        offset = 0

    if not isinstance(min_part_count,int):
        min_part_count = 0
    
    if not isinstance(max_part_count,int):
        max_part_count = 100000

    toffset = offset
    offset = (offset - 1) * limit if offset > 0 else 0

    
    if sort_by == sort_byp:
        if sort_dir == 'asc':
            sort_dir = 'desc'
        else:
            sort_dir = 'asc'
    else:
        sort_dir = 'asc'

    def arrow(name):
        if request.args.get('sort_by','set_name') == name:
            if request.args.get('sort_dir','asc') == 'asc':
                return '▲' 
            else:
                return '▼'
        else:
            return ''
            
    params = [sort_dir, set_name, theme_name, min_part_count, max_part_count, limit,toffset]
    names = ["sort_dir","set_name","theme_name","min_part_count","max_part_count","limit"]

    link = f'http://127.0.0.1:5000/sets?set_name={set_name}&theme_name={theme_name}&min_part_count={min_part_count}&max_part_count={max_part_count}&limit={limit}&sort_dir={sort_dir}&offset={toffset}'

    query = f"""select set.set_num as set_num, set.name as set_name, set.year as year, theme.name as theme_name, count(set.num_parts) as part_count, set.starred as star
                from set
                join theme on set.theme_id= theme.id
                join inventory on set.set_num = inventory.set_num 
                join inventory_part on inventory.id = inventory_part.inventory_id
                where set.name ilike %(set_name)s and theme.name ilike %(theme_name)s
                group by set.set_num, set_name, year, theme.name
                having count(set.num_parts) > %(min_part_count)s and count(set.num_parts) < %(max_part_count)s
                order by {sort_by} {sort_dir}
                """
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                            {query} limit %(limit)s 
                            offset %(offset)s
                        """,
                        {
                        "set_name": f'%{set_name}%',
                        "theme_name": f"%{theme_name}%",
                        "min_part_count": min_part_count,
                        "max_part_count": max_part_count,
                        "limit": limit,
                        "offset": offset
                    })        
            result = list(cur.fetchall())
    except Exception as e:
        conn.rollback()  # Rollback the transaction
        print(f"Error: {e}")
    
    with conn.cursor() as cur:
        cur.execute(f"select count(*) as num from ({query}) as sub",
                    {
                    "set_name": f'%{set_name}%',
                    "theme_name": f"%{theme_name}%",
                    "min_part_count": min_part_count,
                    "max_part_count": max_part_count
                })
        num = cur.fetchone()["num"]
    pages = num // limit + 1
    return render_template("sets.html",rows=result,nums=num,link=link,pages=pages,params=params,names=names,sort_by=sort_by)

@app.route("/my-sets", methods=['GET','POST'])
def render_my_sets():
    if request.method == 'POST':
        set_num2 = request.form["set_num2"]
    else:        
        set_num2 = request.args.get("set_num2","")
    
   
    value= True    
        
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
                               num=result_count_r, 
                               rows=results,
                               Value= value,
                               result_count_r=result_count_r)