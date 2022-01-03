import asyncio
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer
from io import BytesIO
import easygui as eg
from tkinter import *
from PIL import Image, ImageTk
from tkscrolledframe import ScrolledFrame
import googlemaps
from googleplaces import GooglePlaces, types, lang
gmaps = googlemaps.Client(key="AIzaSyCDP_SZf59AEsV1ZcSsdr-j9QEgba3w6fY")
import requests, json 
api_key ='AIzaSyCDP_SZf59AEsV1ZcSsdr-j9QEgba3w6fY'
google_places = GooglePlaces("AIzaSyCDP_SZf59AEsV1ZcSsdr-j9QEgba3w6fY")

TITLE = "Poor student's shopping assistant"


SELECTED = None
WALLET = 0
BALANCE = 0
ADD_BUTTON = None
SHOPPING_CART_TRACKER = []
MONEY_WARNING = None
BALANCE_INDICATOR = 0
CHOOSING = True


def on_frame_click(e):
    global SELECTED
    global ADD_BUTTON
    if SELECTED is None:
        SELECTED = e
        e.info.config(background = "lightblue")
        ADD_BUTTON.config(state='normal')
    elif SELECTED == e:
        e.info.config(background = "gainsboro")
        SELECTED = None
        ADD_BUTTON.config(state=DISABLED)
    else:
        SELECTED.info.config(background = "gainsboro")
        SELECTED = e
        e.info.config(background = "lightblue")
        ADD_BUTTON.config(state='normal')


def add_to_cart(shopping_cart):
    global BALANCE
    global MONEY_WARNING
    global SHOPPING_CART_TRACKER
    if SELECTED is not None:
        if BALANCE > 0:
            MONEY_WARNING.pack_forget()
            shopping_cart.insert(END, SELECTED)
            SHOPPING_CART_TRACKER.append(SELECTED)
            BALANCE -= float(SELECTED.get_price())
            print(BALANCE)
            update_balance()
        else:
            MONEY_WARNING.pack(expand=NO, anchor=(W))
            

def remove_from_cart(shopping_cart):
    global BALANCE
    global SHOPPING_CART_TRACKER
    cartitem = shopping_cart.curselection()
    if cartitem:
        for item in SHOPPING_CART_TRACKER:
            if item.get_name() == shopping_cart.get(cartitem):
                BALANCE += float(item.get_price())
                update_balance()
                print(BALANCE)
                SHOPPING_CART_TRACKER.remove(item)
                break
        shopping_cart.delete(cartitem)



def add_money_to_balance(field):
    global BALANCE
    global WALLET
    oldwallet = WALLET
    WALLET = float(field.widget.get())*100
    BALANCE -= oldwallet
    BALANCE += WALLET
    update_balance()



def update_balance():
    global BALANCE
    global BALANCE_INDICATOR
    if BALANCE < 0:
        BALANCE_INDICATOR.config(text="Balance: "+str(BALANCE/100)+" Euros", fg="red")
    else:
        BALANCE_INDICATOR.config(text="Balance: "+str(BALANCE/100)+" Euros", fg="green")


def generate_route():
    global SHOPPING_CART_TRACKER

    address = eg.enterbox("Please enter your address in Tartu", TITLE)
    shop_product = {}
    for product in SHOPPING_CART_TRACKER:
        store = product.get_store()
        store = store.split(",")
        shop_product.update({store[0]: [] })

    for product in SHOPPING_CART_TRACKER:
        name = product.get_name()
        store = product.get_store()
        store = store.split(",")
        shop_product[store[0]].append(name)
    
    destination_addresses = find_shops(address, shop_product.keys())
    
    message = "Your shoplist:\n"
    
    for shop in shop_product.keys():
        message += "    {}\n".format(shop)
        for productlist in shop_product.values():
            if shop_product[shop] == productlist:
                message += "        {}\n".format(productlist)



    for shop in shop_product.keys():
        message += "{} is on address: {}\n".format(shop, destination_addresses[shop])

    print(message)
    eg.msgbox(message, TITLE)


def goback(root):
    root.destroy()


def on_closing(root):
    global CHOOSING
    CHOOSING = False
    root.destroy()


def find_shops(source, shops):
    found_value = {}
    for magaz in shops:
        query_result = google_places.text_search(query=magaz, location = source, radius=100)
        address = ''
        min = 100000000000.00
        for place in query_result.places:
            place.get_details()
            target = place.geo_location
            r = gmaps.distance_matrix(source, target, mode='walking')["rows"][0]["elements"][0]["distance"]["value"]
            obj = str(place)
            fpos = obj.find("lat=")
            objt = obj[fpos+4:len(obj)]
            fpos = objt.find(",")
            objt = float(objt[0:fpos])
            fpos = obj.find("lng=")
            objg = obj[fpos+4:len(obj)]
            fpos = objg.find(",")
            objg = float(objg[0:fpos])
            reverse_geocode_result = gmaps.reverse_geocode((objt, objg))
            x = reverse_geocode_result[0]
            x = x['formatted_address']
            if r<min:
                min = r
                address = x
        found_value.update({magaz : address})
    return found_value


async def fetch(url, session):
    async with session.get(url) as response:
        return await response.read()


async def request_category_dict(language):
    if language == "ru":
        url = "http://www.kriisis.ee/{}/cat_sale.php?catid=1".format(language)
    else:
        url = "http://www.kriisis.ee/cat_sale.php?catid=1"
    
    async with ClientSession() as session:
        async with session.get(url, raise_for_status=True) as response:
            if response.status == 200:
                response = await response.read()
                soup = bs(response, 'html.parser')
                elements = soup.findAll("p", {"class": "shop2"})
                produces = {}
                if elements is not None: 
                    for element in elements:
                        produces.update( {element.get_text() : element.parent.find('a')['href']} )

                    return produces
                else:
                    return None
            else:
                return None


async def request_subproducts(language, category):
    if language == "ru":
        url = "http://www.kriisis.ee/{}/{}".format(language, category)
    else:
        url = "http://www.kriisis.ee/{}".format(category)
    
    async with ClientSession() as session:
        async with session.get(url, raise_for_status=True) as response:
            if response.status == 200:
                response = await response.read()
                soup = bs(response, 'html.parser')

                target = soup.find("a", href=category)

                subproducts = {}
                if target is not None:
                    target = target.parent.findNext('ul').findAll("a", {"class": "left_links2"})
                    for element in target:
                        subproducts.update( {element.get_text() : element['href']} )

                    return subproducts
                else:
                    return None


async def request_produces_list(language, target_url):
    if language == "ru":
        url = "http://www.kriisis.ee/{}/{}".format(language, target_url)
    else:
        url = "http://www.kriisis.ee/{}".format(target_url)
    
    async with ClientSession() as session:
        async with session.get(url, raise_for_status=True) as response:
            if response.status == 200:
                response = await response.read()
                soup = bs(response, 'html.parser') 

                lol = soup.findAll("img", {"class": "img_rate"})

                produces = []
                if lol is not None: 
                    for element in lol:
                        produces.append("http://www.kriisis.ee/"+element.parent['href'])
                    return produces
                else:
                    return None


async def request_produce_information(language, urls):
    tasks = []

    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    async with ClientSession() as session:
        for url in urls:
            task = asyncio.ensure_future(fetch(url, session))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        # you now have all response bodies in this variable
        
        return responses


# multiprocessing would probably work
# beautifulsoups parser is not trivial to speed up
async def process_raw_request_result(raw_request_result):
        tasks = []

        for response in raw_request_result:
            tasks.append(asyncio.create_task(
                process_raw_request(response)))
        products_info_dict = await asyncio.gather(*tasks)
        return products_info_dict


async def process_raw_request(response):
    soup = bs(response, 'html.parser')
    # product_id = url.partition("?id=")[2]
    name = soup.find("h2", {"class": "larger"}).getText()
    img_url = soup.find("img", {"class": "img_big"})['src']
    shop = soup.find("h1", {"class": "big"}).getText().replace("Pood: ", "")
    price = soup.find("p", {"class": "view_sale_date"}).findNext().getText().replace("Hind: ", "").replace("€", "")

    return [name, img_url, shop, price]



class StoreObject():
    def __init__(self, target_container, product_information, nrow):
        self.name = product_information[0]
        self.store = product_information[2]
        self.price = product_information[3]

        self.cell = Frame(target_container,
            width=600,
            height=150,
            borderwidth=3, 
            relief="solid")
        self.cell.grid_propagate(False)

        response = requests.get(product_information[1])
        pilImage = Image.open(BytesIO(response.content))
        pilImage = pilImage.resize((200, 200), Image.ANTIALIAS)
        img= ImageTk.PhotoImage(pilImage)

        self.icon = Label(self.cell, image=img)
        self.icon.image = img
        
        self.info = Label(self.cell, 
            anchor="center",
            justify="center",
            text="{}\n{}\n{}".format(self.name, self.store, self.price+"€"), 
            font=("Courier", 14),
            wraplength=300)
        
        self.info.pack(side=RIGHT, fill=BOTH)
        self.icon.pack(side=LEFT)

        self.cell.bind("<Button-1>", lambda x: on_frame_click(self))
        self.info.bind("<Button-1>", lambda x: on_frame_click(self))
        self.icon.bind("<Button-1>", lambda x: on_frame_click(self))

        self.cell.grid(row=nrow,
            column=1,
            padx=4,
            pady=4,
            sticky=(W, E))

    
    def get_name(self):
        return self.name

    def get_price(self):
        return float(self.price)*100
    
    def get_store(self):
        return self.store
    
    def __str__(self):
        return self.name


class UIComponent():
    def __init__(self, list_of_product_information):
            global ADD_BUTTON
            global MONEY_WARNING
            global BALANCE_INDICATOR
            global WALLET
            global BALANCE

            self.root = Tk()
            self.root.geometry("1200x600")

            self.root.title(TITLE)

            self.root.protocol("WM_DELETE_WINDOW", (lambda: on_closing(self.root)))


            left_big_frame = Frame(self.root, 
                height = 600, 
                width = 600, 
                borderwidth=4, 
                relief="solid")

            left_frame = ScrolledFrame(
                left_big_frame, 
                height = 500, 
                width = 600, 
                borderwidth=4, 
                relief="solid",
                scrollbars="vertical")

            left_frame.pack(side="top", 
                fill=BOTH, 
                expand=NO, 
                padx=10, 
                pady=10)

            right_frame = Frame(self.root,
                borderwidth=4,
                relief="solid")   

            right_frame.pack(side="right",
                fill=BOTH, 
                expand=YES, 
                pady=10)

            shopping_cart_frame = Frame(right_frame, 
                borderwidth=2, 
                relief="solid", 
                highlightbackground="red")

            shopping_cart_frame.pack(side="top", 
                fill=BOTH, 
                expand=1)

            shopscrollbar = Scrollbar(shopping_cart_frame, orient="vertical")
            shopscrollbar.pack(fill=Y, side="right")

            shopping_cart = Listbox(shopping_cart_frame, font=("Courier", 16))
            shopping_cart.pack(side="bottom", 
                fill="both", 
                expand=True)
            
            if SHOPPING_CART_TRACKER:
                for item in SHOPPING_CART_TRACKER:
                    shopping_cart.insert(END, item)

            shopping_cart_header = Label(shopping_cart_frame, 
                text="Shopping Cart", 
                font=("Courier", 22))
            shopping_cart_header.pack(side="top", fill=X)


            sub_frame = Frame(right_frame, 
                height = 100, 
                width = 300, 
                borderwidth=2, 
                relief="solid")

            sub_frame.pack(side="bottom", 
                fill=BOTH, 
                expand=1,  
                padx=3, 
                pady=5)

            money_label = Label(
                sub_frame, 
                text="Money", 
                font=("Courier", 22))
            money_label.pack(expand=NO, anchor=(NE))

            back = Button(sub_frame,
                font=("Courier, 22"),
                text="GO BACK",
                command=(lambda: goback(self.root)))
            
            back.pack(anchor=(NW))

            route = Button(sub_frame,
                font=("Courier, 22"),
                text="Generate Route",
                command=(lambda: generate_route()))
            
            route.pack(anchor=(NW))

            money_field = Entry(sub_frame, 
                font=("Courier", 22),
                width=5)
            money_field.bind("<Return>",  add_money_to_balance)
            money_field.insert(0, str(WALLET if (WALLET == 0) else WALLET/100))
            money_field.pack(expand=NO, anchor=(E))

            MONEY_WARNING = Label(sub_frame, 
                text="NOT ENOUGH MONEY",
                fg="red", 
                font=("Courier bold", 22))
            MONEY_WARNING.pack(expand=NO, anchor=(W))
            MONEY_WARNING.pack_forget()

            BALANCE_INDICATOR = Label(sub_frame, 
                text="Balance: "+str(BALANCE if (BALANCE == 0) else BALANCE/100)+" Euros",
                fg="GREEN", 
                font=("Courier bold", 22))
            BALANCE_INDICATOR.pack(expand=NO, anchor=(S))

            inner_frame = left_frame.display_widget(Frame)

            left_big_frame.pack(
                fill=BOTH, 
                expand=YES, 
                padx=10, 
                pady=10)
            
            self.store_objects = []
            
            n = 0
            for val in list_of_product_information:
                self.store_objects.append(StoreObject(inner_frame, val, n))
                n += 1

            ADD_BUTTON = Button(left_big_frame, 
                state=DISABLED, 
                font=("Courier", 22), 
                text="ADD", 
                command= (lambda: add_to_cart(shopping_cart)))

            ADD_BUTTON.pack(side="bottom")

            DEL_BUTTON = Button(sub_frame,
                font=("Courier, 22"),
                text="Remove from cart",
                command= (lambda: remove_from_cart(shopping_cart)))
            DEL_BUTTON.pack(side="bottom")

            self.root.mainloop()



def main():
    global SELECTED
    global CHOOSING

    CHOOSING = True

    while CHOOSING:
        language = eg.buttonbox("Choose a language", TITLE, choices = ["EE", "RU"])
        if language == None:
            break
        else:
            language = language.lower()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # request 1
        future = asyncio.ensure_future(request_category_dict(language))
        loop.run_until_complete(future)
        dict_of_categories = future.result()

        if not dict_of_categories:
            sys.exit()
        
        choice = eg.choicebox("Select a category", TITLE, dict_of_categories.keys())

        if not choice:
            sys.exit()

        # request 2
        future = asyncio.ensure_future(
            request_subproducts(language, dict_of_categories[choice]))
        loop.run_until_complete(future)
        dict_of_subcategories = future.result()
        

        choice2 = eg.choicebox("Select a subcategory", TITLE, dict_of_subcategories.keys())

        if not choice2:
            sys.exit()

        # request 3
        future = asyncio.ensure_future(
            request_produces_list(language, dict_of_subcategories[choice2]))
        loop.run_until_complete(future)
        list_of_produce_links = future.result()

        
        # request 4
        future = asyncio.ensure_future(
            request_produce_information(language, list_of_produce_links))
        loop.run_until_complete(future)
        raw_request_result = future.result()

        list_of_product_information = asyncio.run(
            process_raw_request_result(raw_request_result))

        # display it in UI
        # choosing = False
        manager = UIComponent(list_of_product_information)
        del manager
        SELECTED = None
        
        if CHOOSING == False:
            sys.exit()


if __name__ == "__main__":
    main()

