
# Object Oriented Programming in Python
# =====================================
# 
# Object Oriented Programming (OOP) is a great way to organize your code.
# 
# Benefits
# --------
# 
# - namespace control
# - easier for testing
# - partitions code into manageable pieces
# - basis for modules and submodules
# - eliminates redundancy
# 
# Drawbacks
# ---------
# 
# - more planning
# - learning new (and unfamiliar) syntax
# - difficult to parallelize
# - may sacrifice computational efficiency
# - some projects don't require OOP

# Concepts
# ========
# 
# - namespaces (binding methods and attributes to an object)
# - the self (first argument in method calls)
# - initialization
# - inheritance

# In[7]:

import numpy as np
from scipy.optimize import minimize

np.random.seed(1234)
np.set_printoptions(precision=2, suppress=True)

class World(object):
    '''an economic world
    
    ** Attributes **
    
    skill_price : float
        the price per unit of skill
    types : list
        list of floats, determines disutility of investment (learning)
    discount : float
        discount rate
    world_id : int
        id of world
    '''
    
    totalworlds = 0
    
    def __init__(self, skill_price, types, discount):
        self.skill_price = skill_price
        self.types = types
        self.discount = discount
        self.agents = []
        World.totalworlds += 1
        self.world_id = World.totalworlds
    
    def add_agent(self, agent=None):
        '''adds an agent to the world
        
        Parameters
        ----------
        agent : Agent instance or None
            if None, creates an agent
        '''
        
        if agent is not None:
            assert isinstance(agent, Agent)
            if agent.world is not self:
                raise ValueError('agent cannot be added to two worlds')
                
            self.agents.append(agent)
        else:
            self.agents.append(Agent(self))
    
    def __str__(self):
        string = 'World No. {}\n'.format(self.world_id)
        string += '**********************************************\n'
        string += 'Price Per Unit Skill: {}\n\n'.format(self.skill_price)
        string += 'Discount Rate: {}\n\n'.format(self.discount)
        string += 'Utility Per Unit Investment:\n'
        string += '    Type 0: {}\n'.format(self.types[0])
        string += '    Type 1: {}\n\n'.format(self.types[1])
        string += 'Number of Agents: {}\n'.format(len(self.agents))
    
        return string

world1 = World(1., [-0.1, 0.1], 0.95)
print world1


# Out[7]:

#     World No. 1
#     **********************************************
#     Price Per Unit Skill: 1.0
#     
#     Discount Rate: 0.95
#     
#     Utility Per Unit Investment:
#         Type 0: -0.1
#         Type 1: 0.1
#     
#     Number of Agents: 0
#     
# 

# In[8]:

class Agent(object):
    '''an economic agent
    
    ** Attributes **
    
    endowment : float
        initial set of a 1-dimensional skill
    type_ : int
        1 if enjoys learning, 0 if does not enjoy learning
    controls : dict
        flow of investments and consumption (as np arrays)
    state : dict
        flow of skills
    world : World instance
        a world containing certain exogenous parameters
    agent_id : int
        id of agent in world
    '''
    
    A = 10
    
    def __init__(self, world):
        self.endowment = np.random.uniform(low=0,high=1,size=1)[0]
        self.type_ = np.random.choice([0,1], 1)[0]
        self.controls = {'Investments':None,'Consumption':None}
        self.state = {'Skills':None, 'Earnings':None, 'Utility':None}
        self.world = world
        world.add_agent(self)
        self.agent_id = len(world.agents)

    def technology(self, C, I):
        '''flow of lifetime skills
        
        Parameters
        ----------
        C : np.ndarray
            flow of consumption
        I : np.ndarray
            flow of investments
            
        Returns
        -------
        skills : np.ndarray
            flow of lifetime skills
        '''
        
        skills = [self.endowment]
        
        assert isinstance(I, np.ndarray)
        
        for i in I:
            skills.append(skills[-1] + i)
        
        return np.array(skills[:-1])
        
    def earnings(self, skills):
        '''earnings in current state and skill price
        
        Parameters
        ----------
        skills : np.ndarray
            flow of skills over the lifetime
        
        Returns
        -------
        earnings : np.ndarray
            flow of earnings
        '''
        
        assert isinstance(skills, np.ndarray)
        
        return skills*self.world.skill_price
    
    def utility(self, C, I):
        '''lifetime utility
        
        Parameters
        ----------
        C : np.ndarray
            flow of consumption
        I : np.ndarray
            flow of investments
        
        Returns
        -------
        utility : float
            utility
        '''
        assert isinstance(C, np.ndarray)
        assert isinstance(I, np.ndarray)
        assert len(C) == len(I)
        
        total = C + self.world.types[self.type_]*I
        
        discounts = np.array([self.world.discount]*len(total))
        
        total = total*(discounts**(np.arange(0,len(total))))
        return total.sum()
    
    def optimize(self):
        '''optimizes utility subject to budget across a lifetime'''
        
        def budget(controls):
            '''budget constraint, for optimizer'''
  
            I = controls[:Agent.A]
            C = controls[Agent.A:]
            
            skills = self.technology(C, I)
            
            earnings = self.earnings(skills)
            
            return earnings - I - C
        
        def lifetime_utility(controls):
            '''lifetime utility, for optimizer'''

            I = controls[:Agent.A]
            C = controls[Agent.A:]
            
            return -self.utility(C, I)
        
        # initial guess for control variables
        I0 = np.array([0.]*Agent.A)
        skills = np.array([self.endowment]*Agent.A)
        earnings = self.earnings(skills)
        C0 = earnings - I0
        init = np.hstack((I0,C0))
        
        # bounds and constraints
        bnds =  [(0,None)]*len(init)
        con = {'type':'eq', 'fun':budget}
        
        
        res = minimize(fun=lifetime_utility, x0=init, constraints=con,                        bounds=bnds, method='SLSQP')
        
        # saving data
        I = res.x[:Agent.A]
        C = res.x[Agent.A:]
        skills = self.technology(C, I)
        earnings = self.earnings(skills)
        utility = self.utility(C,I)
        self.controls['Investments'] = I
        self.controls['Consumption'] = C
        self.state['Skills'] = skills
        self.state['Earnings'] = earnings
        self.state['Utility'] = utility

    def __str__(self):
        string = 'Agent No. {} of World No. {}\n'.format(self.agent_id, self.world.world_id)
        string += '*****************************************************\n'
        string += 'Agent Type: {}\n'.format(self.type_)
        string += 'Investments:\n{}\n\n'.format(self.controls['Investments'])
        string += 'Consumption:\n{}\n\n'.format(self.controls['Consumption'])
        string += 'Skills:\n{}\n\n'.format(self.state['Skills'])
        string += 'Earnings:\n{}\n\n'.format(self.state['Earnings'])
        string += 'Total Present Discounted Utility:\n{}\n\n'.format(self.state['Utility'])
        
        return string

peter = Agent(world1)
print world1

peter.optimize()
print peter

amy = Agent(world1)
print world1

amy.optimize()
print amy

world2 = World(2.3, [-0.4, 0.9], 0.35)
print world2

lucifer = Agent(world2)
lucifer.optimize()
print lucifer

        


# Out[8]:

#     World No. 1
#     **********************************************
#     Price Per Unit Skill: 1.0
#     
#     Discount Rate: 0.95
#     
#     Utility Per Unit Investment:
#         Type 0: -0.1
#         Type 1: 0.1
#     
#     Number of Agents: 1
#     
#     Agent No. 1 of World No. 1
#     *****************************************************
#     Agent Type: 0
#     Investments:
#     [  0.19   0.38   0.77   1.53   3.06   6.13  12.26  24.51   0.     0.  ]
#     
#     Consumption:
#     [ -0.    -0.    -0.     0.    -0.     0.     0.     0.    49.03  49.03]
#     
#     Skills:
#     [  0.19   0.38   0.77   1.53   3.06   6.13  12.26  24.51  49.03  49.03]
#     
#     Earnings:
#     [  0.19   0.38   0.77   1.53   3.06   6.13  12.26  24.51  49.03  49.03]
#     
#     Total Present Discounted Utility:
#     59.8344999477
#     
#     
#     World No. 1
#     **********************************************
#     Price Per Unit Skill: 1.0
#     
#     Discount Rate: 0.95
#     
#     Utility Per Unit Investment:
#         Type 0: -0.1
#         Type 1: 0.1
#     
#     Number of Agents: 2
#     
#     Agent No. 2 of World No. 1
#     *****************************************************
#     Agent Type: 0
#     Investments:
#     [   0.82    1.64    3.27    6.54   13.09   26.17   52.34  104.68    0.
#         0.  ]
#     
#     Consumption:
#     [  -0.     -0.     -0.     -0.      0.      0.     -0.      0.    209.37
#       209.37]
#     
#     Skills:
#     [   0.82    1.64    3.27    6.54   13.09   26.17   52.34  104.68  209.37
#       209.37]
#     
#     Earnings:
#     [   0.82    1.64    3.27    6.54   13.09   26.17   52.34  104.68  209.37
#       209.37]
#     
#     Total Present Discounted Utility:
#     255.509056994
#     
#     
#     World No. 2
#     **********************************************
#     Price Per Unit Skill: 2.3
#     
#     Discount Rate: 0.35
#     
#     Utility Per Unit Investment:
#         Type 0: -0.4
#         Type 1: 0.9
#     
#     Number of Agents: 0
#     
#     Agent No. 1 of World No. 2
#     *****************************************************
#     Agent Type: 1
#     Investments:
#     [    1.81     5.96    19.67    64.91   214.22   706.91     7.76    15.77
#         19.27  1208.27]
#     
#     Consumption:
#     [   -0.      -0.       0.       0.      -0.       0.    2325.05  2334.9
#       2367.65  1222.99]
#     
#     Skills:
#     [    0.79     2.59     8.55    28.22    93.14   307.35  1014.27  1022.03
#       1037.79  1057.07]
#     
#     Earnings:
#     [    1.81     5.96    19.67    64.91   214.22   706.91  2332.81  2350.67
#       2386.93  2431.26]
#     
#     Total Present Discounted Utility:
#     20.9290738875
#     
#     
# 

# Inheritance
# -----------
# 
# What if we wanted to change the technology without writing redundant code? Easy, use a subclass! Very different from just writing a function with many options. Remember that using namespaces many function parameters are kept "under the hood", within the object's namespace.

# In[9]:

class HealthAgent(Agent):
    
    def __init__(self,world):
        Agent.__init__(self,world)
    
    def technology(self, I, C):
        '''flow of lifetime skills
        
        Parameters
        ----------
        I : np.ndarray
            flow of investments
        C : np.ndarray
            flow of consumption
            
        Returns
        -------
        skills : np.ndarray
            flow of lifetime skills
        '''
        
        skills = [self.endowment]
        
        assert isinstance(I, np.ndarray)
        
        for i,c in zip(I,C):
            
            skills.append(skills[-1] + i*c)
        
        return np.array(skills[:-1])   


# In[10]:

pat = HealthAgent(world1)
pat.optimize()

print pat


# Out[10]:

#     Agent No. 3 of World No. 1
#     *****************************************************
#     Agent Type: 1
#     Investments:
#     [   0.49    0.45    0.74    0.98    1.09    1.81    3.71   11.4    78.26
#       618.14]
#     
#     Consumption:
#     [    0.37     0.59     0.57     0.75     1.38     2.15     4.13    11.79
#         79.34  5748.61]
#     
#     Skills:
#     [    0.86     1.04     1.31     1.73     2.46     3.96     7.85    23.19
#        157.6   6366.72]
#     
#     Earnings:
#     [    0.86     1.04     1.31     1.73     2.46     3.96     7.85    23.19
#        157.6   6366.72]
#     
#     Total Present Discounted Utility:
#     3737.52396398
#     
#     
# 

# In[10]:



