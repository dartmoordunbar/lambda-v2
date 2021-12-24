import psycopg2, pandas

conn = psycopg2.connect("postgres://postgres:S3vgvCA2fQdCccg@pg-1.ctnxr0jdghs2.eu-west-1.rds.amazonaws.com/mapapp")
def getTable(type, aoi_id, tableObject=None):

    if type == 'nts-recreation-visitor-count':
        sql = f"""
            select ac.name, ac.id, (dcnr.visitors::int * 1000) as visitors
            from aoi_client ac 
            join "data-client-nts-recreation" dcnr on dcnr.aoi_id = ac.id
            where id = {aoi_id}
        """
        df = pandas.read_sql(sql, conn)
        if df.empty:
            return None
        else:
            visitors = df['visitors'][0]
            return visitors

