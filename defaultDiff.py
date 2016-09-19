import os
from xml.etree import ElementTree
import csv
from flask import Flask, request, make_response, send_file, render_template
app = Flask(__name__)
dict = {}
dict1 = {}


class DictDiffer(object):
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect
    def removed(self):
        return self.set_past - self.intersect
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])

def get_properties(mo, mo_name):
    if 'prop' in mo.tag :
        key = mo.attrib['name']
        value = mo.attrib['value']
        dict[mo_name][key] = value
    elif 'child' in mo.tag :
        for child in mo.getchildren():
            #child_name = child.attrib['class']
            get_properties(child, mo_name)

def get_properties1(mo, mo_name):
    if 'prop' in mo.tag :
        key = mo.attrib['name']
        value = mo.attrib['value']
        dict1[mo_name][key] = value
    elif 'child' in mo.tag :
        for child in mo.getchildren():
            #child_name = child.attrib['class']
            get_properties1(child, mo_name)


@app.route("/")
def welcome():
    return render_template('welcome.html')
    # return '<form action="/parser" method="post" > <label> Enter XML Name of First Release </label> <input type="text" ' \
    #        'name="firstxml" /> <br/><br/><label> Enter XML Name of Second Release </label> <input type="text" ' \
    #        'name="secondxml" /><br/><br/> <input type="submit"> </form>'

@app.route("/parser", methods=['POST'])
def echo():
    file1= request.form['firstxml']
    file2 = request.form['secondxml']
    dom = ElementTree.parse(file1)
    dom1 = ElementTree.parse(file2)

    for mo in dom.findall('.//child'):
        mo_name = mo.attrib['class']
        dn = mo.find('prop[@name="name"]')
        if dn is not None:
            dn_name=dn.attrib['value']
            mo_name = mo_name + dn_name
        dict[mo_name]={}
        children = mo.getchildren()
        for child in children:
            get_properties(child,mo_name)

    for mo in dom1.findall('.//child'):
        mo_name = mo.attrib['class']
        dn = mo.find('prop[@name="name"]')
        if dn is not None:
            dn_name=dn.attrib['value']
            mo_name = mo_name + dn_name
        dict1[mo_name]={}
        children = mo.getchildren()
        for child in children:
            get_properties1(child,mo_name)
    d = DictDiffer(dict1, dict)
    added = d.added()
    removed = d.removed()
    changed = d.changed()
    changed_prop = None
    added_prop = None
    removed_prop = None


    # Dump the ones which got added new in Release
    w = csv.writer(open("Added_Defaults.csv", "w"))
    w.writerow(["    MO_NAME    ", "    PROPERTY    ", "    VALUE    "])

    for i in added:
        w.writerow([])
        for key,val in dict1[i].items():
            w.writerow([i, key, val])

    w = csv.writer(open("Removed_Defaults.csv", "w"))
    w.writerow(["    MO_NAME    ", "    PROPERTY    ", "    VALUE    "])

    for i in removed:
        w.writerow([])
        for key,val in dict[i].items():
            w.writerow([i, key, val])

    w = csv.writer(open("Changed_Defaults.csv", "w"))
    w.writerow(["    MO_NAME    ", "    PROPERTY    ", "    VALUE for First XML    ","    VALUE for Second XML    "])
    decor = "-------------"
    for i in changed:
        d1 = DictDiffer(dict1[i], dict[i])
        added_prop = d1.added()
        changed_prop = d1.changed()
        removed_prop = d1.removed()

        w.writerow([])
        for key in added_prop:
            w.writerow([i, key, "<Property Not Present>",dict1[i][key] ])
        for key in changed_prop:
            w.writerow([i, key, dict[i][key], dict1[i][key]])
        for key in removed_prop:
            w.writerow([i, key,  dict[i][key],"<Propery Not Present>"])

    html = ''
    html += '<p> The CSV downloaded will contain list of Default Policy MOs where there is difference in properties' \
            ' between two releases. The difference can be change in value, addition of new property or removal' \
            ' of property. Use Visore.xml to get more detail/info about the MO shown in csv. ' \
            'Contact Dev why the change is done for particular policy, identify the impact and test over ' \
            'the changed areas </p>'
    html += '<a href="/download_changed/" target="blank"><button> Changed Default Policies </button></a><br/><br/>'
    return html

           #'<a href="/download_new/" target="blank"><button> New Default Policies </button></a><br/><br/>' \
           #'<a href="/download_removed/" target="blank"><button> Removed Default Policies </button></a>'

@app.route("/download_changed/")
def download_changed():
    try:
        path = os.path.abspath("Changed_Defaults.csv")
        return send_file(path, attachment_filename='Changed_Defaults.csv')
    except Exception as e:
        print str(e)

@app.route("/download_removed/")
def download_removed():
    try:
        path = os.path.abspath("Removed_Defaults.csv")
        return send_file(path, attachment_filename='Removed_Defaults.csv')

    except Exception as e:
        print str(e)

@app.route("/download_new/")
def download_new():
    try:
        path = os.path.abspath("Added_Defaults.csv")
        return send_file(path, attachment_filename='Added_Defaults.csv')

    except Exception as e:
        print str(e)



if __name__ == "__main__":
    app.run()









