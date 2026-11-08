# Meeting Notes

Kept by Andy. Newest stuff goes at the top. I'm trying to keep what we actually **decided** separate from what we just **talked about**, so nobody writes in their paper that something was decided when it was only an idea.

Anything marked `[fill in]` still needs details from whoever was there.

## Who's who

- **CSE Team #35:** Andy Vo (team manager), Khaled Khan, Parth Sachdev, Jason Grewal, Amareen Singh. Faculty advisor: Dr. Yuan Hong.
- **ECE Team 2721:** Jubei Ellis (team manager), Lefteris (Eleftherios) Tsikis (camera / detection hardware), Zihang Yang. Prof. Shalabh Gupta is on their emails.
- **Sponsor:** Holly Beum, Interface Technologies.

## What we've decided so far

- **Nov 4, 2026** (Jubei and Andy with both teams, confirmed by Holly over email): we're meeting Holly in person on **Mon Nov 9 at 3:30 PM in ITE C19**, which is where last year's system is. Holly is out of state after Nov 10 until Nov 23, so this is the last in-person chance before Thanksgiving.
- **Nov 2, 2026** (Jubei, in Discord): the budget numbers are two different things. The $150 is Holly's per-unit target for the finished product (it would retail for about $300), and she calls it a "straw man" number, so it's a direction and not a hard cap. The $500 is separate and is only for buying materials to build the prototype.
- **Nov 2, 2026** (Andy, in Discord): no CSE team meeting this week. Everyone is working on their own part of the paper, and we'll all meet with Holly on the 9th.
- **Around Nov 1, 2026** (team, from the work plan in the group chat): we split into five lanes for the first 7-page drafts. Andy does coordination and docs, Khaled does camera research, Parth does the backend, Jason does the YOLO model, and Amareen does the dashboard.
- **Oct 28, 2026** (team): our repo is `pks0916/senior-design`, and changes go in through pull requests. Parth's backend fixes were the first one (PR #1).
- **Oct 19, 2026** (Dr. Hong, advisor meeting): this fall we each write a 15-page paper, the paper gets reviewed, and we do a presentation on what we got done this semester.
- **Oct 19, 2026** (Dr. Hong, advisor meeting): we can use AI tools however we want for the class deliverables.
- **[fill in]**: CSE handles the software (model, backend, dashboard) and ECE handles the hardware. This is how both teams have been working, and Lefteris is doing the camera on the ECE side, but I still need to find when it was officially decided.

## Camera: still being discussed (not decided)

This has been going back and forth between the two teams, so here's where it stands:

- **Oct 21–23:** Lefteris emailed asking whether we'd picked a camera. Jubei had mentioned we were looking at a doorbell-style camera with AI detection. Khaled replied pointing Lefteris to the email we'd already sent with our camera preference, based on what the software needs.
- **Earlier idea (CSE):** an off-the-shelf security/IP camera like the Reolink RLC-811A (RTSP, PoE, infrared night vision). Khaled also remembered Holly mentioning she'd used a Wyze doorbell cam for testing before.
- **Late Oct / early Nov (ECE):** when ECE talked to Prof. Gupta about the camera, he suggested going with a bare OEM camera module, because it's cheaper and getting the video data off it is simpler. Lefteris also asked how we'd even pull the video off the security camera we picked.
- **Nov 2 (Jubei):** pointed out the security camera would eat most of the $150 per-unit target.
- **Nov 2 (Amareen):** the OEM module works for us and fits the $150 target better. With the security camera we'd have pulled video over RTSP on the network, but a module plugged straight into the Pi is simpler for our code anyway. For the model to pick up bears consistently, the camera needs:
  - night vision: a NoIR module (no IR filter), plus a separate IR light from ECE
  - Pi compatibility: a CSI ribbon or USB connection
  - at least 1080p
  - decent low-light performance
  - weatherproofing isn't needed on the camera itself, since the enclosure can handle it
- **Nov 2 (Andy and Khaled):** we also pointed out that with the $500 prototype budget we can start with something a bit pricier for testing and then get cheaper, since you don't usually go straight from one or two prototypes to a production design. Khaled went through the options ECE sent and said the best fit for us is the **Raspberry Pi Camera Module 3 Wide NoIR plus the 36-LED IR board**.
- **Still open:** ECE needs to pick the final model and send it to us so we can check it works with our code. This should probably get settled at the Nov 9 meeting.

## Stuff we still need to figure out

- [ ] Exact due dates for the 7-page draft, the review, the final paper, and the presentation (ask Dr. Hong)
- [ ] Who's reviewing the paper: Dr. Hong, the writing instructor, or each other? (ask Dr. Hong)
- [ ] Final camera model, and whether it's the Camera Module 3 Wide NoIR + IR board (ECE, hopefully at the Nov 9 meeting)
- [ ] What counts as success: detection distance, false alarms, response time? (ask Holly on Nov 9)
- [ ] Does last year's IACUC approval for testing on wild bears carry over to us? (ask Dr. Hong or Dr. Rittenhouse)
- [x] ~~Is the budget really around $500, and what is it for?~~ Answered Nov 2: $500 is for prototype materials, and $150 is the per-unit target (see above)

## Meetings and threads

### Nov 9, 2026, 3:30 PM: In-person meeting with Holly (both teams), ITE C19
- Who was there: [fill in after]
- What we talked about: [fill in after]
- What we decided: [fill in after]
- To-dos: [fill in after]

### Oct 27 – Nov 4, 2026: Scheduling the meeting with Holly (email + Discord)
- Oct 27: Jubei emailed Holly a project update. ECE now has last year's (2025–26) unit and is going through its design, looking at options to improve it while keeping cost down. Jubei asked to set up the next meeting.
- Oct 28: Holly said she'd prefer to meet in person and listed the dates she's free on campus (Oct 29, 30 and Nov 2, 6, 9, 10). After that she's out of state until the 23rd.
- Oct 31: in Discord, Khaled said Mon Nov 9 would be best, and Jubei and Zihang agreed.
- Nov 1: Andy emailed Holly confirming Nov 9 for both teams. Holly said any time that day works for her.
- Nov 3: we figured out times in Discord. Khaled asked for 3:30 PM, and Jubei, Zihang, and Andy were all fine with it. Jubei suggested ITE C19 since that's where the system is.
- Nov 4: Jubei emailed Holly with 3:30 PM in ITE C19, and Holly confirmed.

### Oct 21–23, 2026: Camera emails with ECE
- Lefteris reached out to Andy about the camera choice and followed up on Oct 23 with some cheaper options.
- Khaled replied that our camera preference and the software specs were in the email we'd already sent.
- Nothing was decided. See the camera section above for where it went from there.

### [fill in date]: First meeting with Holly Beum (sponsor)
- Who was there: [fill in]
- What we talked about: introductions. Holly mentioned she'd used a Wyze doorbell cam for testing before. [fill in anything else]
- What we decided: nothing final. We agreed to set up a longer in-person meeting.
- To-dos: [fill in]

### Oct 19, 2026: Meeting with Dr. Hong (advisor)
- Who was there: [fill in]
- What we talked about: what the class expects from us this semester
- What we decided: three deliverables (15-page paper, paper review, semester presentation), and AI use is allowed
- Still open: due dates and who reviews the paper

### [fill in date]: CSE and ECE meeting
- Who was there: [fill in]
- What we talked about: possible design changes, making the system more portable, and using an off-the-shelf smart/IP camera (RTSP, PoE, infrared night vision) instead of building our own. Khaled brought up the Reolink RLC-811A as an option.
- What we decided: nothing final on the camera (see the camera section above)

## Template

```
### YYYY-MM-DD: <meeting>
- Who was there:
- What we talked about:
- What we decided:
- To-dos (who, by when):
```
