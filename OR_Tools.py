import tkinter as tk
from tkinter import filedialog
from tkinter import *
import csv
from ortools.sat.python import cp_model
import collections

root= tk.Tk()
root.title("Computational Scheduling by PS_O5")

canvas1 = tk.Canvas(root, width = 300, height = 300, bg = 'black')
canvas1.pack()

def getfile ():
	global jd, op
	import_file_path = filedialog.askopenfilename()
	with open(import_file_path) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=",")
		jd = [[tuple(map(int, row[i : i + 2])) for i in range(0, len(row), 2) ] for row in csv_reader ]
def close_win(): 
    root.destroy()
    
browse = tk.Button(text='Import Schedule File', command=getfile, bg='gray', fg='white', font=('helvetica', 11, 'bold'))
canvas1.create_window(150, 150, window=browse)

start = tk.Button(text='Start Scheduling', command=close_win, bg='gray', fg='white', font=('helvetica', 11, 'bold'))
canvas1.create_window(150, 250, window=start)

logo = PhotoImage(file="a.ppm")
canvas1.create_image(30,20, image=logo)

    
root.mainloop()
	
	
def MinimalJobshopSat():

    model = cp_model.CpModel()

    jobs_data = jd

    machines_count = 1 + max(task[0] for job in jobs_data for task in job)
    all_machines = range(machines_count)


    horizon = sum(task[1] for job in jobs_data for task in job)


    task_type = collections.namedtuple('task_type', 'start end interval')

    assigned_task_type = collections.namedtuple('assigned_task_type', 'start job index duration')

    all_tasks = {}
    machine_to_intervals = collections.defaultdict(list)

    for job_id, job in enumerate(jobs_data):
        for task_id, task in enumerate(job):
            machine = task[0]
            duration = task[1]
            suffix = '_%i_%i' % (job_id, task_id)
            start_var = model.NewIntVar(0, horizon, 'start' + suffix)
            end_var = model.NewIntVar(0, horizon, 'end' + suffix)
            interval_var = model.NewIntervalVar(start_var, duration, end_var,
                                                'interval' + suffix)
            all_tasks[job_id, task_id] = task_type(start=start_var,
                                                   end=end_var,
                                                   interval=interval_var)
            machine_to_intervals[machine].append(interval_var)

    for machine in all_machines:
        model.AddNoOverlap(machine_to_intervals[machine])

    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job) - 1):
            model.Add(all_tasks[job_id, task_id +
                                1].start >= all_tasks[job_id, task_id].end)

    obj_var = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(obj_var, [
        all_tasks[job_id, len(job) - 1].end
        for job_id, job in enumerate(jobs_data)
    ])
    model.Minimize(obj_var)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:

        assigned_jobs = collections.defaultdict(list)
        for job_id, job in enumerate(jobs_data):
            for task_id, task in enumerate(job):
                machine = task[0]
                assigned_jobs[machine].append(
                    assigned_task_type(start=solver.Value(
                        all_tasks[job_id, task_id].start),
                                       job=job_id,
                                       index=task_id,
                                       duration=task[1]))


        output = ''
        for machine in all_machines:

            assigned_jobs[machine].sort()
            sol_line_tasks = 'Machine ' + str(machine) + ': '
            sol_line = '           '

            for assigned_task in assigned_jobs[machine]:
                name = 'job_%i_%i' % (assigned_task.job, assigned_task.index)

                sol_line_tasks += '%-20s' % name

                start = assigned_task.start
                duration = assigned_task.duration
                sol_tmp = '[%i,%i]' % (start, start + duration)

                sol_line += '%-20s' % sol_tmp

            sol_line += '\n'
            sol_line_tasks += '\n'
            output += sol_line_tasks
            output += sol_line

        print('Optimal Schedule Length: %i' % solver.ObjectiveValue())
        print(output)
        sch = open("computed_schedule.txt", "x")
        sch.write('Optimal Schedule Length: %i' % solver.ObjectiveValue()+'\n\n')
        sch.write(output)
        sch.close()
        
MinimalJobshopSat()

