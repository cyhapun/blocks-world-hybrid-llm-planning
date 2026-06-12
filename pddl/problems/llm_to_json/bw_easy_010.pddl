(define (problem bw_easy_010)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on c a)
    (clear b)
    (clear c)
    (handempty)
  )

  (:goal
    (on a b)
  )
)
