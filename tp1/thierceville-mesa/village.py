from enum import unique
import math
import random
from re import L
import numpy as np
from collections import defaultdict

import uuid
import mesa
import numpy
import pandas
import matplotlib.pyplot as plt
from mesa import space
from mesa.batchrunner import BatchRunner
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import ModularServer, VisualizationElement
from mesa.visualization.modules import ChartModule

from mesa.visualization.ModularVisualization import UserSettableParameter

class ContinuousCanvas(VisualizationElement):
    local_includes = [
        "./js/simple_continuous_canvas.js",
    ]

    def __init__(self, canvas_height=500,
                 canvas_width=500, instantiate=True):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.identifier = "space-canvas"
        if (instantiate):
            new_element = ("new Simple_Continuous_Module({}, {},'{}')".
                           format(self.canvas_width, self.canvas_height, self.identifier))
            self.js_code = "elements.push(" + new_element + ");"

    def portrayal_method(self, obj):
        return obj.portrayal_method()

    def render(self, model):
        representation = defaultdict(list)
        for obj in model.schedule.agents:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.pos[0] - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.pos[1] - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        
        return representation

def wander(x, y, speed, model):
    r = random.random() * math.pi * 2
    new_x = max(min(x + math.cos(r) * speed, model.space.x_max), model.space.x_min)
    new_y = max(min(y + math.sin(r) * speed, model.space.y_max), model.space.y_min)

    return new_x, new_y

def count_human(model):
    '''
    count the number of human in the model
    '''
    cpt = 0
    for agent in model.schedule.agent_buffer():
        if agent.lp == False:
            cpt += 1
    return cpt


def count_lycanthrope(model):
    '''
    count the number of lycanthrope in the model
    '''
    cpt = 0
    for agent in model.schedule.agent_buffer():
        if agent.lp == True:
            cpt += 1
    return cpt

def count__transformed_lycanthrope(model):
    '''
    count the number of transformed lycanthrope in the model
    '''
    cpt = 0
    for agent in model.schedule.agent_buffer():
        if agent.lp and agent.lyco_transformed:
            cpt += 1
    return cpt

class  Village(mesa.Model):
    def  __init__(self,  n_villagers,n_lp,n_cleric,n_hunter):
        mesa.Model.__init__(self)
        self.space = mesa.space.ContinuousSpace(600, 600, False)
        self.schedule = RandomActivation(self)
        for  _  in  range(n_villagers):
            self.schedule.add(Villager(random.random()  *  600,  random.random()  *  600,  10, uuid.uuid1(), self,loup_garou=False))
        for  _  in  range(n_lp):
            self.schedule.add(Villager(random.random()  *  600,  random.random()  *  600,  10, uuid.uuid1(), self,loup_garou=True))
        for  _  in  range(n_cleric):
            self.schedule.add(Cleric(random.random()  *  600,  random.random()  *  600,  10, uuid.uuid1(), self,loup_garou=False))
        for  _  in  range(n_hunter):
            self.schedule.add(Hunter(random.random()  *  600,  random.random()  *  600,  10, uuid.uuid1(), self,loup_garou=False))
        self.dc = DataCollector(model_reporters={"human_count": [count_human,[self]], "lycanthrope_count": [count_lycanthrope,[self]], 
        "transformed_lycanthrope_count":[count__transformed_lycanthrope,[self]], "agent_count": lambda m : m.schedule.get_agent_count()   })

    def step(self):
        self.dc.collect(self)
        self.schedule.step()

        if self.schedule.steps >= 1000:
            self.running = False






class Villager(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village, distance_attack=40, p_attack=0.6,loup_garou=False):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
        self.distance_attack = distance_attack
        self.p_attack = p_attack
        self.lp = loup_garou
        self.r = 3
        self.lyco_transformed = False

    def portrayal_method(self):
        # r = 3
        if self.lp == True:
            color = "red"
        else:
            color = "blue"
        
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": self.r}
        return portrayal

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)
        self.transform()
        
    def transform(self):
        if self.lp == True:
            if random.random() < 0.1 and self.lyco_transformed == False:
                self.r = 6
                self.lyco_transformed = True
            if self.lyco_transformed == True and random.random() < self.p_attack:
                self.attack()
                
    
    def attack(self):
        villager_attackable = [ villager for villager in self.model.schedule.agent_buffer() if ( villager.lp == False) and  (( (villager.pos[0] - self.pos[0] ) **2) + ( (villager.pos[1] - self.pos[1]) ** 2 ) ) < self.distance_attack**2 ]
        # We attack someone randomly from the list:
        # print(len(villager_attackable))
        if len(villager_attackable) != 0:
            vil = np.random.choice(villager_attackable)
            vil.lp = True


class Cleric(Villager):
    def __init__(self, x, y, speed, unique_id: int, model: Village, distance_savable=30, p_save=0.6,loup_garou=False):
        super(Villager,self).__init__(unique_id, model)
        Villager.__init__(self,x,y,speed,unique_id,model)      
        self.distance_savable = distance_savable
        self.p_save = p_save

    def portrayal_method(self):
        if self.lp == True:
            color = "red"
        else:
            color = "green"
        
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": self.r}
        return portrayal

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)
        self.transform()

        if random.random() < self.p_save and self.lp == False: 
            villager_savable = [ villager for villager in self.model.schedule.agent_buffer() if villager.lyco_transformed == False and (( (villager.pos[0] - self.pos[0] ) **2) + ( (villager.pos[1] - self.pos[1]) ** 2 ) ) < (self.distance_savable)**2 ]
            #We save someone randomly from the list:
            if len(villager_savable ) != 0:
                vil = np.random.choice(villager_savable)
                vil.lp = False


class Hunter(Villager):
    def __init__(self, x, y, speed, unique_id: int, model: Village, distance_huntable=40, p_hunt=0.6,loup_garou=False):
        super(Villager,self).__init__(unique_id, model)
        Villager.__init__(self,x,y,speed,unique_id,model) 
        self.distance_huntable = distance_huntable
        self.p_hunt = p_hunt

    def portrayal_method(self):
        if self.lp == True:
            color = "red"
        else:
            color = "black"
        
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": self.r}
        return portrayal

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)

        self.transform()


        if random.random() < self.p_hunt and self.lp == False: 

            lyco_huntable = [ lyco for lyco in self.model.schedule.agent_buffer() if lyco.lyco_transformed == True and (( (lyco.pos[0] - self.pos[0] ) **2) + ( (lyco.pos[1] - self.pos[1]) ** 2 ) ) < (self.distance_huntable)**2 ]
            # We hunt a lyco randomly from the list:
            if len(lyco_huntable) != 0:
                lyco = np.random.choice(lyco_huntable)
                self.model.schedule.remove(lyco)




def run_single_server():
    
    chart = ChartModule([{"Label": "human_count", "Color": "Blue"},{"Label": "lycanthrope_count", "Color": "Red"},
    {"Label": "transformed_lycanthrope_count", "Color": "Purple"},{"Label": "agent_count", "Color": "Yellow"}],
    data_collector_name= 'dc',canvas_height=200,canvas_width=500)

    n_villagers_slider = UserSettableParameter('slider',"Number of villagers", 20, 0, 100, 1)
    n_lycanthropes_slider = UserSettableParameter('slider',"Number of lycanthropes", 5, 0, 100, 1)
    n_clerics_slider = UserSettableParameter('slider',"Number of clerics", 1, 0, 100, 1)
    n_hunters_slider = UserSettableParameter('slider',"Number of hunters", 2, 0, 100, 1)


    server  =  ModularServer(Village, [ContinuousCanvas(),chart],"Village",{"n_villagers":  n_villagers_slider,"n_lp":n_lycanthropes_slider,
     "n_cleric":n_clerics_slider,"n_hunter":n_hunters_slider})
    server.port = 8521
    server.launch()

def run_batch():
    params_dict = {
    'n_villagers': [50],
    'n_lp' : [5],
    'n_hunter' : [1],
    'n_cleric' : range(0,6,1) }

    br = BatchRunner(Village,params_dict,
    model_reporters=
    {"human_count": lambda m : count_human(m) , "lycanthrope_count": lambda m : count_lycanthrope(m), 
    "transformed_lycanthrope_count": lambda m : count__transformed_lycanthrope(m),
    "agent_count": lambda m : m.schedule.get_agent_count()   })
    
    br.run_all()
    df = br.get_model_vars_dataframe()
    print(df)
    df[['human_count','lycanthrope_count','transformed_lycanthrope_count','agent_count']].plot()
    plt.show()



if  __name__  ==  "__main__":
    # server  =  ModularServer(Village, [ContinuousCanvas(),chart],"Village",{"n_villagers":  n_villagers_slider,"n_lp":n_lycanthropes_slider,
    #  "n_cleric":n_clerics_slider,"n_hunter":n_hunters_slider})
    # server.port = 8521
    # server.launch()

    # run_batch()

    run_single_server()
